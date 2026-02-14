import asyncio
import sys
import os

# Add project root
sys.path.append(os.getcwd())

from backend.database import search_recipes

async def main():
    print("--- Verifying 'Drinks' Search ---")
    try:
        # Search using the modified logic (q matches name OR tag)
        res = await search_recipes(q="Drinks")
        print(f"Total Found: {res['total']}")
        
        if res['total'] > 0:
            print("Success! Found recipes.")
            # Print first few
            for r in res['recipes'][:3]:
                print(f"- {r['name']} (Tags: {', '.join(r['tags'])})")
        else:
            print("Failure. Found 0 recipes.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
