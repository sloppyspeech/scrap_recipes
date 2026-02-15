import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db
from backend.rag import RAGSystem

async def main():
    print("Generating partial embeddings for testing...")
    rag = RAGSystem()
    db = await get_db()
    try:
        # Get 10 recipes
        cursor = await db.execute("SELECT id, name FROM recipes LIMIT 10")
        rows = await cursor.fetchall()
        recipes = []
        for row in rows:
            r_id, r_name = row
            ing_cursor = await db.execute("SELECT name FROM ingredients WHERE recipe_id = ?", [r_id])
            ingredients = [r[0] for r in await ing_cursor.fetchall()]
            tag_cursor = await db.execute("SELECT t.name FROM tags t JOIN recipe_tags rt ON t.id = rt.tag_id WHERE rt.recipe_id = ?", [r_id])
            tags = [r[0] for r in await tag_cursor.fetchall()]
            
            recipes.append({
                "id": r_id, "name": r_name, "ingredients": [{"name": i} for i in ingredients], "tags": tags
            })
            
        await rag.index_recipes(recipes)
        print("Partial indexing complete.")
        
        # Test Query
        print("\nTesting Search: 'recipe'")
        results = await rag.search("recipe")
        print(f"Found {len(results)} results: {results}")
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
