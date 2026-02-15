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
    
    # Fetch all recipes using the shared function
    from backend.database import get_all_recipes
    recipes = await get_all_recipes()
            
    print(f"Fetched {len(recipes)} recipes from database.")
    
    # Generate embeddings
    # Note: index_recipes now uses ChromaDB and batch processing
    await rag.index_recipes(recipes)
    print("Embedding refresh complete!")

if __name__ == "__main__":
    asyncio.run(main())
