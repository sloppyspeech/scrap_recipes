import asyncio
import sys
import os
import json
sys.path.append(os.getcwd())
from backend.database import search_recipes

async def main():
    print("Auditing 'buttermilk' recipes...")
    # Get generic buttermilk recipes
    # Note: search_recipes default behavior is text search on 'q'
    res = await search_recipes(q="buttermilk")
    
    with open("buttermilk_audit.txt", "w", encoding="utf-8") as f:
        f.write(f"Query: 'buttermilk'\n")
        f.write(f"Total: {res['total']}\n")
        for r in res['recipes']:
            f.write(f"- {r['name']}\n")
            f.write(f"  Tags: {r['tags']}\n")
            
    print("Audit complete. Check buttermilk_audit.txt")

if __name__ == "__main__":
    asyncio.run(main())
