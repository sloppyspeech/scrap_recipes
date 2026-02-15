"""
Import recipes from the JSON file into the SQLite database.
Run once: python import_data.py
"""
import json
import sqlite3
import os
import sys
import re
import argparse

# Path configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
JSON_FILE = os.path.join(PROJECT_ROOT, "recipes_all_from_p1_20260214_1050.json")
DB_PATH = os.path.join(SCRIPT_DIR, "recipes.db")


def parse_calories_numeric(cal_str: str) -> float | None:
    """Extract numeric calories from strings like '108 calories' or '4012 Cal'."""
    if not cal_str:
        return None
    match = re.search(r'([\d.]+)', str(cal_str))
    return float(match.group(1)) if match else None


def import_recipes():
    """Import all recipes from JSON into SQLite."""
    print(f"Reading JSON: {JSON_FILE}")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Found {len(data)} recipes in JSON")

    # Remove existing DB if present
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing DB: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create schema
    cursor.executescript("""
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
    """)

    # Create FTS tables
    cursor.executescript("""
        CREATE VIRTUAL TABLE IF NOT EXISTS recipes_fts USING fts5(name, content='recipes', content_rowid='id');
        CREATE VIRTUAL TABLE IF NOT EXISTS ingredients_fts USING fts5(name, content='ingredients', content_rowid='id');
    """)

    # Create triggers for FTS sync
    cursor.executescript("""
        CREATE TRIGGER IF NOT EXISTS recipes_ai AFTER INSERT ON recipes BEGIN
            INSERT INTO recipes_fts(rowid, name) VALUES (new.id, new.name);
        END;
        CREATE TRIGGER IF NOT EXISTS ingredients_ai AFTER INSERT ON ingredients BEGIN
            INSERT INTO ingredients_fts(rowid, name) VALUES (new.id, new.name);
        END;
    """)

    conn.commit()

    # Tag cache: name -> id
    tag_cache = {}
    recipe_count = 0
    ingredient_count = 0
    tag_count = 0
    skipped = 0

    for entry in data:
        recipe = entry.get("Recipe", {})
        name = recipe.get("Name", "").strip()
        url = recipe.get("Url", "").strip()

        if not name or not url:
            skipped += 1
            continue

        times = recipe.get("Times", {})
        nutrients = recipe.get("NutrientValues", {})
        calories_raw = recipe.get("Calories", "")
        calories_numeric = parse_calories_numeric(calories_raw)

        try:
            cursor.execute(
                """INSERT INTO recipes (name, url, makes, calories_raw, calories_numeric,
                   soaking_time, preparation_time, cooking_time, baking_time,
                   baking_temperature, sprouting_time, total_time, nutrient_values)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    name, url,
                    recipe.get("Makes", ""),
                    calories_raw,
                    calories_numeric,
                    times.get("SoakingTime", ""),
                    times.get("PreparationTime", ""),
                    times.get("CookingTime", ""),
                    times.get("BakingTime", ""),
                    times.get("BakingTemperature", ""),
                    times.get("SproutingTime", ""),
                    times.get("TotalTime", ""),
                    json.dumps(nutrients) if nutrients else None,
                )
            )
            recipe_id = cursor.lastrowid
            recipe_count += 1
        except sqlite3.IntegrityError:
            # Duplicate URL, skip
            skipped += 1
            continue

        # Insert ingredients
        for ing in recipe.get("Ingredients", []):
            if not isinstance(ing, dict):
                continue
            ing_name = str(ing.get("Name", "") or "").strip()
            ing_qty = str(ing.get("Quantity", "") or "").strip()
            if ing_name:
                cursor.execute(
                    "INSERT INTO ingredients (recipe_id, name, quantity) VALUES (?, ?, ?)",
                    (recipe_id, ing_name, ing_qty)
                )
                ingredient_count += 1

        # Insert tags
        for tag_name in recipe.get("Tags", []):
            tag_name = tag_name.strip()
            if not tag_name:
                continue

            if tag_name not in tag_cache:
                try:
                    cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                    tag_cache[tag_name] = cursor.lastrowid
                    tag_count += 1
                except sqlite3.IntegrityError:
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                    tag_cache[tag_name] = cursor.fetchone()[0]

            cursor.execute(
                "INSERT OR IGNORE INTO recipe_tags (recipe_id, tag_id) VALUES (?, ?)",
                (recipe_id, tag_cache[tag_name])
            )

        # Insert categories
        # Cache: name -> id
        if 'category_cache' not in locals():
            category_cache = {}
            category_count = 0

        for cat_name in recipe.get("Categories", []):
            cat_name = cat_name.strip()
            if not cat_name:
                continue

            if cat_name not in category_cache:
                try:
                    cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
                    category_cache[cat_name] = cursor.lastrowid
                    category_count += 1
                except sqlite3.IntegrityError:
                    cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
                    res = cursor.fetchone()
                    if res:
                        category_cache[cat_name] = res[0]
                    else:
                        continue # Should not happen

            cursor.execute(
                "INSERT OR IGNORE INTO recipe_categories (recipe_id, category_id) VALUES (?, ?)",
                (recipe_id, category_cache[cat_name])
            )

    conn.commit()
    conn.close()

    print(f"\n✅ Import complete!")
    print(f"   Recipes:     {recipe_count}")
    print(f"   Ingredients: {ingredient_count}")
    print(f"   Tags:        {tag_count}")
    print(f"   Categories:  {category_count if 'category_count' in locals() else 0}")
    print(f"   Skipped:     {skipped}")
    print(f"   DB path:     {DB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import recipes from JSON to SQLite')
    parser.add_argument('json_file', nargs='?', default=JSON_FILE,
                        help='Path to JSON file to import (default: configured in script)')
    args = parser.parse_args()
    
    # Override JSON_FILE global if arg provided
    if args.json_file:
        JSON_FILE = args.json_file
        
    import_recipes()
