import asyncio
import json
import sys
import os

# Add project root
sys.path.append(os.getcwd())

from backend.database import search_recipes, init_db, get_all_tags
from backend.ollama_client import extract_search_filters

async def debug():
    # Ensure DB is initialized (though likely already is)
    # await init_db() 
    
    print("--- Debugging Natural Search ---")

    # Check tags
    tags = await get_all_tags()
    print(f"Total Tags: {len(tags)}")
    print(f"Top 5 Tags: {[t['name'] for t in tags[:5]]}")

    queries = [
        "buttermilk",
        "drinks with buttermilk"
    ]
    
    # Test multi-tag directly
    # ...

    for q in queries:
        print(f"\nQuery: '{q}'")
        
        # 1. Test LLM Extraction
        print("  Asking extraction...")
        filters = {}
        try:
            filters = await extract_search_filters(q)
            print(f"  Extracted Filters: {json.dumps(filters, indent=2)}")
        except Exception as e:
            print(f"  Extraction Error: {e}")
            continue

        # 2. Test DB Search
        print("  Searching DB...")
        try:
            # Wrap single tag in list
            tags = []
            if filters.get("tag"):
                tags.append(filters["tag"])

            results = await search_recipes(
                q=filters.get("q", ""),
                include_ingredients=filters.get("include_ingredients", []),
                exclude_ingredients=filters.get("exclude_ingredients", []),
                tags=tags,
                cal_min=filters.get("cal_min"),
                cal_max=filters.get("cal_max")
            )
            print(f"  Found: {results['total']} recipes")
            if results['recipes']:
                print("  Results:")
                for r in results['recipes']:
                    # Print simplified info
                    print(f"  - {r['name']}")
                    print(f"    Tags: {r['tags']}")
        except Exception as e:
            print(f"  DB Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug())
