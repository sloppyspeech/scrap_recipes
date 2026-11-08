import asyncio
import os
import sys

sys.path.append(os.getcwd())
from scripts.populate_calories import normalize_batch, CALORIE_DB

async def test():
    batch = ["salt", "sugar", "onion", "garam masala", "chicken"]
    data = await normalize_batch(batch)
    print("Normalized:", data)
    for item in data:
        clean = item.get("clean", "").strip()
        cal = CALORIE_DB.get(clean)
        if cal is None:
            if "Flour" in clean: cal = 360
            elif "Dal" in clean: cal = 340
            elif "Oil" in clean: cal = 884
            elif "Masala" in clean: cal = 300
            else: cal = 0
        print(f"{clean} -> {cal}")

asyncio.run(test())
