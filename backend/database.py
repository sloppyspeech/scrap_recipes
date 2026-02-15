"""
SQLite database setup and query helpers for the Recipe UI application.
Uses aiosqlite for async access from FastAPI.
"""
import aiosqlite
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "recipes.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS recipes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    url                 TEXT NOT NULL UNIQUE,
    makes               TEXT,
    calories_raw        TEXT,
    calories_numeric    REAL,
    soaking_time        TEXT,
    preparation_time    TEXT,
    cooking_time        TEXT,
    baking_time         TEXT,
    baking_temperature  TEXT,
    sprouting_time      TEXT,
    total_time          TEXT,
    nutrient_values     TEXT
);

CREATE TABLE IF NOT EXISTS ingredients (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    name      TEXT NOT NULL,
    quantity  TEXT
);

CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS recipe_tags (
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    tag_id    INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (recipe_id, tag_id)
);

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS recipe_categories (
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (recipe_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(name);
CREATE INDEX IF NOT EXISTS idx_recipes_calories ON recipes(calories_numeric);
CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name);
CREATE INDEX IF NOT EXISTS idx_ingredients_recipe ON ingredients(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_tags_recipe ON recipe_tags(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_tags_tag ON recipe_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_recipe_categories_recipe ON recipe_categories(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_categories_category ON recipe_categories(category_id);
"""

FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS recipes_fts USING fts5(name, content='recipes', content_rowid='id');
CREATE VIRTUAL TABLE IF NOT EXISTS ingredients_fts USING fts5(name, content='ingredients', content_rowid='id');
"""

FTS_TRIGGERS_SQL = """
CREATE TRIGGER IF NOT EXISTS recipes_ai AFTER INSERT ON recipes BEGIN
    INSERT INTO recipes_fts(rowid, name) VALUES (new.id, new.name);
END;
CREATE TRIGGER IF NOT EXISTS ingredients_ai AFTER INSERT ON ingredients BEGIN
    INSERT INTO ingredients_fts(rowid, name) VALUES (new.id, new.name);
END;
"""


def parse_calories_numeric(cal_str: str) -> float | None:
    """Extract numeric calories value from strings like '108 calories' or '4012 Cal'."""
    if not cal_str:
        return None
    import re
    match = re.search(r'([\d.]+)', cal_str)
    if match:
        return float(match.group(1))
    return None


async def get_db() -> aiosqlite.Connection:
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Initialize the database schema."""
    db = await aiosqlite.connect(DB_PATH)
    await db.executescript(SCHEMA_SQL)
    await db.executescript(FTS_SQL)
    await db.executescript(FTS_TRIGGERS_SQL)
    await db.commit()
    await db.close()


async def search_recipes(
    q: str = "",
    include_ingredients: list[str] = None,
    exclude_ingredients: list[str] = None,
    tags: list[str] = None,
    category: str = "",
    cal_min: float = None,
    cal_max: float = None,
    nutrient: str = "",
    nutrient_max: float = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    Search recipes with multiple filters. Returns list of recipe dicts + total count.
    """
    db = await get_db()
    try:
        conditions = []
        params = []

        if q:
            # FTS5 query for names (extract words)
            fts_query = q.replace('"', '').strip() + '*'
            
            # Tag partial match
            tag_query = f"%{q.strip()}%"

            conditions.append(f"""
                (r.id IN (SELECT rowid FROM recipes_fts WHERE recipes_fts MATCH ?)
                 OR r.id IN (SELECT rt.recipe_id FROM recipe_tags rt 
                             JOIN tags t ON rt.tag_id = t.id 
                             WHERE t.name LIKE ?))
            """)
            params.append(fts_query)
            params.append(tag_query)

        # Handle multiple included ingredients (AND logic)
        if include_ingredients:
            for ing in include_ingredients:
                if not ing.strip():
                    continue
                conditions.append(
                    "r.id IN (SELECT recipe_id FROM ingredients i2 "
                    "JOIN ingredients_fts ON ingredients_fts.rowid = i2.id "
                    "WHERE ingredients_fts MATCH ?)"
                )
                fts_ing = ing.replace('"', '').strip() + '*'
                params.append(fts_ing)

        # Handle excluded ingredients (NOT IN logic)
        if exclude_ingredients:
            for ing in exclude_ingredients:
                if not ing.strip():
                    continue
                conditions.append(
                    "r.id NOT IN (SELECT recipe_id FROM ingredients i3 "
                    "JOIN ingredients_fts ON ingredients_fts.rowid = i3.id "
                    "WHERE ingredients_fts MATCH ?)"
                )
                fts_ing = ing.replace('"', '').strip() + '*'
                params.append(fts_ing)

        # Handle multiple tags (AND logic)
        if tags:
            for t_name in tags:
                if not t_name or not t_name.strip():
                    continue
                conditions.append(
                    "r.id IN (SELECT recipe_id FROM recipe_tags rt "
                    "JOIN tags t ON rt.tag_id = t.id "
                    "WHERE t.name = ?)"
                )
                params.append(t_name)

        if category:
            conditions.append(
                "r.id IN (SELECT recipe_id FROM recipe_categories rc "
                "JOIN categories c ON rc.category_id = c.id "
                "WHERE c.name = ?)"
            )
            params.append(category)

        if cal_min is not None:
            conditions.append("r.calories_numeric >= ?")
            params.append(cal_min)

        if cal_max is not None:
            conditions.append("r.calories_numeric <= ?")
            params.append(cal_max)

        if nutrient and nutrient_max is not None:
            # Search within JSON nutrient_values for a specific nutrient
            conditions.append("r.nutrient_values IS NOT NULL")

        where = " AND ".join(conditions) if conditions else "1=1"

        # Count query
        count_sql = f"SELECT COUNT(*) FROM recipes r WHERE {where}"
        cursor = await db.execute(count_sql, params)
        row = await cursor.fetchone()
        total = row[0]

        # Data query
        offset = (page - 1) * page_size
        data_sql = f"""
            SELECT r.id, r.name, r.url, r.makes, r.calories_raw, r.calories_numeric,
                   r.total_time, r.nutrient_values
            FROM recipes r
            WHERE {where}
            ORDER BY r.name
            LIMIT ? OFFSET ?
        """
        cursor = await db.execute(data_sql, params + [page_size, offset])
        rows = await cursor.fetchall()

        recipes = []
        for row in rows:
            recipe = {
                "id": row[0],
                "name": row[1],
                "url": row[2],
                "makes": row[3],
                "calories": row[4],
                "calories_numeric": row[5],
                "total_time": row[6],
                "nutrient_values": json.loads(row[7]) if row[7] else {},
            }
            # Get tags for this recipe
            tag_cursor = await db.execute(
                "SELECT t.name FROM tags t JOIN recipe_tags rt ON t.id = rt.tag_id WHERE rt.recipe_id = ?",
                [row[0]]
            )
            tag_rows = await tag_cursor.fetchall()
            recipe["tags"] = [t[0] for t in tag_rows]
            recipes.append(recipe)

        # Post-filter by nutrient if needed
        if nutrient and nutrient_max is not None:
            filtered = []
            for r in recipes:
                nv = r.get("nutrient_values", {})
                val_str = nv.get(nutrient, "")
                if val_str:
                    import re
                    m = re.search(r'([\d.]+)', str(val_str))
                    if m and float(m.group(1)) <= nutrient_max:
                        filtered.append(r)
            recipes = filtered

        return {"recipes": recipes, "total": total, "page": page, "page_size": page_size}
    finally:
        await db.close()


async def get_recipe_by_id(recipe_id: int):
    """Get full recipe details by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM recipes WHERE id = ?", [recipe_id]
        )
        row = await cursor.fetchone()
        if not row:
            return None

        recipe = {
            "id": row[0],
            "name": row[1],
            "url": row[2],
            "makes": row[3],
            "calories": row[4],
            "calories_numeric": row[5],
            "times": {
                "soaking_time": row[6],
                "preparation_time": row[7],
                "cooking_time": row[8],
                "baking_time": row[9],
                "baking_temperature": row[10],
                "sprouting_time": row[11],
                "total_time": row[12],
            },
            "nutrient_values": json.loads(row[13]) if row[13] else {},
        }

        # Get ingredients
        cursor = await db.execute(
            "SELECT name, quantity FROM ingredients WHERE recipe_id = ?", [recipe_id]
        )
        ing_rows = await cursor.fetchall()
        recipe["ingredients"] = [{"name": r[0], "quantity": r[1]} for r in ing_rows]

        # Get tags
        cursor = await db.execute(
            "SELECT t.name FROM tags t JOIN recipe_tags rt ON t.id = rt.tag_id WHERE rt.recipe_id = ?",
            [recipe_id]
        )
        tag_rows = await cursor.fetchall()
        recipe["tags"] = [t[0] for t in tag_rows]

        # Get categories
        cursor = await db.execute(
            "SELECT c.name FROM categories c JOIN recipe_categories rc ON c.id = rc.category_id WHERE rc.recipe_id = ?",
            [recipe_id]
        )
        cat_rows = await cursor.fetchall()
        recipe["categories"] = [c[0] for c in cat_rows]

        return recipe
    finally:
        await db.close()


async def get_all_tags():
    """Get all unique tags."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT t.name, COUNT(rt.recipe_id) as count FROM tags t "
            "JOIN recipe_tags rt ON t.id = rt.tag_id "
            "GROUP BY t.name ORDER BY count DESC"
        )
        rows = await cursor.fetchall()
        return [{"name": row[0], "count": row[1]} for row in rows]
    finally:
        await db.close()


async def get_all_categories():
    """Get all unique categories."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT c.name, COUNT(rc.recipe_id) as count FROM categories c "
            "JOIN recipe_categories rc ON c.id = rc.category_id "
            "GROUP BY c.name ORDER BY c.name ASC"
        )
        rows = await cursor.fetchall()
        return [{"name": row[0], "count": row[1]} for row in rows]
    finally:
        await db.close()


async def get_all_recipes():
    """Get all recipes with ingredients and tags for indexing."""
    db = await get_db()
    try:
        # Get basic info
        cursor = await db.execute("SELECT id, name, url FROM recipes")
        rows = await cursor.fetchall()
        
        recipes = []
        for row in rows:
            recipe = {
                "id": row[0],
                "name": row[1],
                "url": row[2],
                "ingredients": [],
                "tags": []
            }
            # Get ingredients for this recipe
            ing_cursor = await db.execute(
                "SELECT name FROM ingredients WHERE recipe_id = ?", 
                [row[0]]
            )
            ing_rows = await ing_cursor.fetchall()
            recipe["ingredients"] = [{"name": r[0]} for r in ing_rows]
            
            # Get tags
            tag_cursor = await db.execute(
                "SELECT t.name FROM tags t JOIN recipe_tags rt ON t.id = rt.tag_id WHERE rt.recipe_id = ?",
                [row[0]]
            )
            tag_rows = await tag_cursor.fetchall()
            recipe["tags"] = [t[0] for t in tag_rows]
            
            recipes.append(recipe)
            
        return recipes
    finally:
        await db.close()
