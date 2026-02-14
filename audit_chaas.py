import asyncio
import sys
import os
import sqlite3
sys.path.append(os.getcwd())

async def main():
    print("Auditing 'Chaas' ingredients...")
    # Direct DB query
    conn = sqlite3.connect('backend/recipes.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM recipes WHERE name LIKE '%Chaas%' LIMIT 1")
    row = cursor.fetchone()
    if row:
        rid, name = row
        print(f"Recipe: {name}")
        cursor.execute("SELECT name, quantity FROM ingredients WHERE recipe_id = ?", (rid,))
        ings = cursor.fetchall()
        print("Ingredients:")
        for i in ings:
            print(f"- {i[0]} : {i[1]}")
    else:
        print("Chaas not found")
        
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
