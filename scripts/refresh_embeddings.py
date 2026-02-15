import asyncio
import os
import sys

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db
from backend.rag import RAGSystem

async def main():
    print("Starting embedding refresh...")
    rag = RAGSystem()
    
    # Fetch all recipes with ingredients and tags
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, name FROM recipes")
        rows = await cursor.fetchall()
        recipes = []
        
        for row in rows:
            r_id, r_name = row
            # Get ingredients
            ing_cursor = await db.execute(
                "SELECT name FROM ingredients WHERE recipe_id = ?", [r_id]
            )
            ingredients = [r[0] for r in await ing_cursor.fetchall()]
            
            # Get tags
            tag_cursor = await db.execute(
                "SELECT t.name FROM tags t JOIN recipe_tags rt ON t.id = rt.tag_id WHERE rt.recipe_id = ?",
                [r_id]
            )
            tags = [r[0] for r in await tag_cursor.fetchall()]
            
            recipes.append({
                "id": r_id,
                "name": r_name,
                "ingredients": [{"name": i} for i in ingredients],
                "tags": tags
            })
            
        print(f"Fetched {len(recipes)} recipes from database.")
        
        # Generate embeddings
        await rag.index_recipes(recipes)
        print("Embedding refresh complete!")
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
