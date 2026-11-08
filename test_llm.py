import asyncio
import os
import sys

sys.path.append(os.getcwd())
from backend.ollama_client import chat_completion

async def test():
    prompt = 'Normalize these ingredients strictly to JSON:\n["sugar", "salt", "apple"]'
    system = """
    You are a culinary data expert. 
    Your task is to Normalize ingredient names to a standard singular form (Title Case) that likely exists in a standard calorie database.
    Also categorize them.
    
    Return a JSON ARRAY of objects.
    """
    response = await chat_completion(prompt, model="qwen3.5:cloud", system=system)
    print("LLM replied:", response)

asyncio.run(test())
