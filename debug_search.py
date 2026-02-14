import asyncio
import json
import sys
import os

# Add project root
sys.path.append(os.getcwd())

from backend.database import search_recipes, init_db
from backend.ollama_client import extract_search_filters

async def debug():
    # Ensure DB is initialized (though likely already is)
    # await init_db() 
    
    queries = [
        "dosa",
        "dosa without rice",
        "spicy potato"
    ]

    print("--- Debugging Natural Search ---")
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        
        # 1. Test LLM Extraction
        print("  Asking LLM...")
        try:
            filters = await extract_search_filters(q)
            print(f"  Extracted Filters: {json.dumps(filters, indent=2)}")
        except Exception as e:
            print(f"  LLM Error: {e}")
            continue

        # 2. Test DB Search
        print("  Searching DB...")
        try:
            results = await search_recipes(
                q=filters.get("q", ""),
                include_ingredients=filters.get("include_ingredients", []),
                exclude_ingredients=filters.get("exclude_ingredients", []),
                tag=filters.get("tag", ""),
                cal_min=filters.get("cal_min"),
                cal_max=filters.get("cal_max")
            )
            print(f"  Found: {results['total']} recipes")
            if results['recipes']:
                print(f"  Top 3: {[r['name'] for r in results['recipes'][:3]]}")
        except Exception as e:
            print(f"  DB Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug())
