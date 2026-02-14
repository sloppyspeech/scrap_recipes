"""
Ollama API client for recipe summarization and ingredient scaling.
Connects to local Ollama instance on port 11435.
"""
import httpx
import json
import re

OLLAMA_BASE_URL = "http://localhost:11435"
DEFAULT_MODEL = "lfm2.5-thinking:latest"

# Global active model (can be changed via admin API)
_active_model = DEFAULT_MODEL


def get_active_model() -> str:
    return _active_model


def set_active_model(model: str):
    global _active_model
    _active_model = model


async def list_models() -> list[dict]:
    """List available Ollama models."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return data.get("models", [])
        except Exception as e:
            return [{"error": str(e)}]


async def chat_completion(prompt: str, model: str = None, system: str = None) -> str:
    """Send a prompt to Ollama and return the response text."""
    model = model or get_active_model()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
            }
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")


async def summarize_recipe(page_text: str, recipe_name: str) -> str:
    """Use LLM to summarize a recipe page."""
    system = (
        "You are a helpful cooking assistant. Summarize the recipe in a clear, "
        "structured format with sections: Overview, Key Ingredients, Steps Summary, "
        "and Tips. Keep it concise but informative. Do not use markdown headers larger than h3."
    )
    prompt = (
        f"Please summarize the following recipe for '{recipe_name}':\n\n"
        f"{page_text[:8000]}"  # Limit to avoid token overflow
    )
    return await chat_completion(prompt, system=system)


async def scale_with_llm(
    ingredients: list[dict],
    original_servings: str,
    target_servings: int,
) -> list[dict]:
    """Use LLM to scale ingredient quantities."""
    system = (
        "You are a precise cooking assistant. Scale the ingredient quantities exactly. "
        "Return ONLY a valid JSON array of objects with 'name' and 'quantity' fields. "
        "No extra text, no markdown, no explanation—just the JSON array."
    )

    ing_text = "\n".join(
        [f"- {i['name']}: {i['quantity']}" for i in ingredients]
    )

    prompt = (
        f"The recipe originally makes: {original_servings}\n"
        f"Scale all ingredients for {target_servings} servings.\n\n"
        f"Original ingredients:\n{ing_text}\n\n"
        f"Return the scaled ingredients as a JSON array."
    )

    response = await chat_completion(prompt, system=system)

    # Try to parse JSON from response
    try:
        # Find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        # If LLM didn't return valid JSON, return original with a note
        return [{"name": i["name"], "quantity": f"{i['quantity']} (scaling failed)"} for i in ingredients]


def scale_algorithmically(
    ingredients: list[dict],
    original_servings_str: str,
    target_servings: int,
) -> list[dict]:
    """Scale ingredients using simple math (no LLM)."""
    # Try to parse original servings count
    original_count = _parse_serving_count(original_servings_str)
    if original_count is None or original_count == 0:
        original_count = 1  # fallback

    ratio = target_servings / original_count
    scaled = []

    for ing in ingredients:
        qty = ing.get("quantity", "")
        scaled_qty = _scale_quantity_string(qty, ratio)
        scaled.append({"name": ing["name"], "quantity": scaled_qty})

    return scaled


def _parse_serving_count(s: str) -> float | None:
    """Extract number from servings string like '4 servings' or '12 dosas'."""
    if not s:
        return None
    match = re.search(r'([\d.]+)', str(s))
    return float(match.group(1)) if match else None


def _scale_quantity_string(qty: str, ratio: float) -> str:
    """Scale a quantity string like '1 1/2 cups' or '1 / 2 cup' by a ratio."""
    if not qty or not qty.strip():
        return qty

    # 1. Normalize fractions with spaces: "1 / 2" -> "1/2", "1 /2" -> "1/2"
    # This fixes the user reported issue with "1 /2 cup"
    qty_norm = re.sub(r'(\d+)\s*/\s*(\d+)', r'\1/\2', qty.strip())

    val = 0.0
    rest = ""
    found = False

    # 2. Try matching different number patterns at the start
    
    # Case A: Mixed fraction "1 1/2"
    match = re.match(r'^(\d+)\s+(\d+/\d+)\s*(.*)$', qty_norm)
    if match:
        whole, frac, r = match.groups()
        n, d = map(float, frac.split('/'))
        val = float(whole) + (n / d)
        rest = r
        found = True
    else:
        # Case B: Simple fraction "1/2"
        match = re.match(r'^(\d+/\d+)\s*(.*)$', qty_norm)
        if match:
            frac, r = match.groups()
            n, d = map(float, frac.split('/'))
            val = n / d
            rest = r
            found = True
        else:
            # Case C: Decimal or Integer "1.5" or "2"
            match = re.match(r'^(\d*\.?\d+)\s*(.*)$', qty_norm)
            if match:
                num, r = match.groups()
                # Skip if it looks like a list item number "1." followed by text? 
                # Ideally we assume quantity starts with amount.
                val = float(num)
                rest = r
                found = True

    if not found:
        return qty

    # 3. Scale and Format
    scaled_val = val * ratio

    # Format nicely
    # If very close to an integer, display as integer
    if abs(scaled_val - round(scaled_val)) < 0.01:
        val_str = str(int(round(scaled_val)))
    else:
        # Show up to 2 decimal places, update to simple fraction if common?
        # For now, just decimal is safer than reconstructing fractions
        val_str = f"{scaled_val:.2f}".rstrip('0').rstrip('.')
    
    return f"{val_str} {rest}".strip()


async def extract_search_filters(query: str) -> dict:
    """Use LLM to extract structured search filters from natural language query."""
    system = (
        "You are a search query parser for a recipe database. "
        "Extract search filters from the user's natural language query. "
        "Return ONLY a valid JSON object used for filtering. "
        "Fields: "
        "'q' (string, main search term like recipe name), "
        "'include_ingredients' (list of strings, ingredients to INCLUDE), "
        "'exclude_ingredients' (list of strings, ingredients to EXCLUDE), "
        "'cal_max' (number, maximum calories, null if unspecified), "
        "'tag' (string, e.g. 'Gluten Free', null if unspecified). "
        "Rules:\n"
        "- If a field is not mentioned, set it to null.\n"
        "- Do NOT return 'None' as a string.\n"
        "- Do NOT halluncinate ingredients not present in the query.\n"
        "Example inputs:\n"
        "- 'dosa with ragi' -> {'q': 'dosa', 'include_ingredients': ['ragi']}\n"
        "- 'no onion garlic recipes' -> {'exclude_ingredients': ['onion', 'garlic']}\n"
        "- 'under 500 calories' -> {'cal_max': 500}\n"
        "- 'simple paneer curry' -> {'q': 'paneer curry'}\n"
    )
    
    prompt = f"Parse this query: '{query}'"
    
    try:
        response = await chat_completion(prompt, system=system)
        
        # Find JSON object in response
        data = {}
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(response)
            
        # Clean up data
        if data.get("tag") == "None" or data.get("tag") == "":
            data["tag"] = None
        if data.get("cal_max") == 0:
            data["cal_max"] = None
        if data.get("cal_min") == 0:
            data["cal_min"] = None
            
        return data
        
    except Exception as e:
        print(f"LLM Extraction failed: {e}")
        # Fallback: treat entire query as text search
        return {"q": query}
