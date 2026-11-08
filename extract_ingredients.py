import asyncio
import os
import sys
import aiosqlite
from collections import Counter

# Add root directory to path to allow imports
sys.path.append(os.getcwd())

DB_PATH = os.path.join(os.path.dirname(__file__), "backend", "recipes.db")

async def extract_ingredients():
    print(f"Connecting to {DB_PATH}...")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT name, quantity FROM ingredients")
        rows = await cursor.fetchall()
        
    print(f"Total ingredient rows: {len(rows)}")
    
    # Count unique names
    names = [row[0].strip().lower() for row in rows]
    counts = Counter(names)
    
    print(f"Unique ingredient names: {len(counts)}")
    
    # Sort by frequency
    sorted_ingredients = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    # Save to file for analysis
    with open("ingredient_analysis.txt", "w", encoding="utf-8") as f:
        f.write(f"Total Rows: {len(rows)}\n")
        f.write(f"Unique Ingredients: {len(counts)}\n\n")
        f.write("--- Top 50 Most Common ---\n")
        for name, count in sorted_ingredients[:50]:
            f.write(f"{name}: {count}\n")
            
        f.write("\n--- All Ingredients (Name: Count) ---\n")
        for name, count in sorted_ingredients:
            f.write(f"{name}: {count}\n")
            
    print("Analysis saved to ingredient_analysis.txt")

if __name__ == "__main__":
    asyncio.run(extract_ingredients())
