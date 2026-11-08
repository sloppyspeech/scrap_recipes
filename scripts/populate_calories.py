import asyncio
import os
import sys
import json
import aiosqlite
import random

# Add root to path
sys.path.append(os.getcwd())

from backend.ollama_client import chat_completion
from backend.database import DB_PATH

# Hardcoded Baseline Calorie Dictionary (per 100g raw/uncooked unless specified)
# Sourced from web research
CALORIE_DB = {
    # Cereals & Grains
    "Rice": 360,
    "Basmati Rice": 360,
    "Brown Rice": 360,
    "Wheat Flour": 340,
    "Atta": 340,
    "Maida": 360,
    "Semolina": 360,
    "Rava": 360,
    "Oats": 389,
    "Besan": 380,
    "Cornflour": 380,
    "Bread": 265,
    
    # Pulses & Legumes
    "Toor Dal": 335,
    "Moong Dal": 340,
    "Chana Dal": 330,
    "Urad Dal": 340,
    "Masoor Dal": 340,
    "Chickpeas": 360, # Kabuli Chana
    "Kidney Beans": 330, # Rajma
    "Soy Chunks": 345,
    
    # Vegetables
    "Onion": 40,
    "Tomato": 18,
    "Potato": 77,
    "Carrot": 41,
    "Spinach": 23,
    "Palak": 23,
    "Cabbage": 25,
    "Cauliflower": 25,
    "Brinjal": 25,
    "Eggplant": 25,
    "Bottle Gourd": 15,
    "Lauki": 15,
    "Capsicum": 20,
    "Green Peas": 81,
    "Coriander": 23,
    "Mint": 40,
    "Ginger": 80,
    "Garlic": 149,
    "Green Chilli": 40,
    "Coconut": 354,
    "Lemon": 29,
    
    # Fats & Oils
    "Oil": 884,
    "Ghee": 900,
    "Butter": 717,
    "Cream": 195,
    
    # Dairy
    "Milk": 60, # approx for whole milk
    "Curd": 98,
    "Yogurt": 60,
    "Paneer": 265,
    "Cheese": 402,
    "Khoya": 420,
    "Mawa": 420,
    
    # Spices & Condiments
    "Salt": 0,
    "Sugar": 387,
    "Jaggery": 383,
    "Turmeric": 350,
    "Chilli Powder": 280,
    "Cumin": 375,
    "Mustard Seeds": 508,
    "Cashew": 553,
    "Almond": 579,
    "Raisins": 299,
    "Peanuts": 567,
    "Sesame": 573,
    "Tamarind": 239,
}

MODEL_NAME = "qwen3.5:cloud"

async def normalize_batch(ingredients):
    system = """
    You are a culinary data expert. 
    Your task is to Normalize ingredient names to a standard singular form (Title Case) that likely exists in a standard calorie database.
    Also categorize them.
    
    Return a JSON ARRAY of objects.
    
    Example Input:
    ["chopped onions", "1 cup milk", "salt to taste"]
    
    Example Output:
    [
      {"original": "chopped onions", "clean": "Onion", "category": "Vegetable"},
      {"original": "1 cup milk", "clean": "Milk", "category": "Dairy"},
      {"original": "salt to taste", "clean": "Salt", "category": "Condiment"}
    ]
    """
    
    prompt = f"Normalize these ingredients strictly to JSON:\n{json.dumps(ingredients)}"
    
    max_retries = 5
    base_delay = 5  # Start with 5 seconds
    
    for attempt in range(max_retries):
        try:
            # Assuming the ollama_client can handle the model name or user has a proxy
            response = await chat_completion(prompt, model=MODEL_NAME, system=system)
            
            # Parse JSON
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end != -1:
                return json.loads(response[start:end])
            return []
            
        except Exception as e:
            err_str = str(e)
            print(f"Error normalizing batch (Attempt {attempt+1}/{max_retries}): {err_str}")
            
            if "429" in err_str or "Too Many Requests" in err_str:
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit hit. Waiting {wait_time:.2f}s before retry...")
                await asyncio.sleep(wait_time)
            else:
                # For non-429 errors, maybe wait a bit less or break? 
                # Let's retry anyway for robustness but with shorter delay
                await asyncio.sleep(2)
                
    print("Max retries reached. Skipping batch.")
    return []

async def populate():
    print("Connecting to DB...")
    async with aiosqlite.connect(DB_PATH) as db:
        # Get processed count
        cursor = await db.execute("SELECT COUNT(*) FROM ingredient_calories")
        row = await cursor.fetchone()
        print(f"Already processed: {row[0]}")
        
        # Get unprocessed unique ingredients
        # Using LEFT JOIN to find missing ones
        sql = """
            SELECT DISTINCT i.name 
            FROM ingredients i
            LEFT JOIN ingredient_calories ic ON i.name = ic.original_name
            WHERE ic.id IS NULL
            LIMIT 50
        """
        # Processing in small batches effectively
        
        while True:
            cursor = await db.execute(sql)
            rows = await cursor.fetchall()
            
            if not rows:
                print("No more ingredients to process.")
                break
                
            batch = [r[0] for r in rows]
            print(f"Processing batch of {len(batch)}: {batch[:3]}...")
            
            normalized_data = await normalize_batch(batch)
            
            if not normalized_data:
                print("Failed to get normalized data. Stopping.")
                break
            
            # Prepare inserts
            inserts = []
            for item in normalized_data:
                orig = item.get("original")
                clean = item.get("clean", "").strip()
                cat = item.get("category", "Unknown")
                
                # Lookup calories
                # Try exact match, then singular/plural check
                cal = CALORIE_DB.get(clean)
                if cal is None:
                    # heuristic fallbacks
                    if "Flour" in clean: cal = 360
                    elif "Dal" in clean: cal = 340
                    elif "Oil" in clean: cal = 884
                    elif "Masala" in clean: cal = 300
                    else: cal = 0 # Unknown
                
                inserts.append((orig, clean, "100 g", cal, cat))
            
            await db.executemany(
                "INSERT OR IGNORE INTO ingredient_calories (original_name, clean_name, quantity_str, calories, category) VALUES (?, ?, ?, ?, ?)",
                inserts
            )
            await db.commit()
            print(f"Inserted {len(inserts)} rows.")
            
            # Sleep to be nice to API
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(populate())
