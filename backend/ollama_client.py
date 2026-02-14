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
    """Scale a quantity string like '1 1/2 cups' by a ratio."""
    if not qty or qty.strip() == "":
        return qty

    # Handle compound fractions: "1 1/2", "2 3/4"
    # Pattern: optional_whole optional_fraction rest
    pattern = r'^(\d+)?\s*(\d+/\d+)?\s*(.*)$'
    match = re.match(pattern, qty.strip())
    if not match:
        return qty

    whole_str, frac_str, rest = match.groups()

    value = 0.0
    has_number = False

    if whole_str:
        value += float(whole_str)
        has_number = True

    if frac_str:
        num, den = frac_str.split('/')
        value += float(num) / float(den)
        has_number = True

    if not has_number:
        return qty

    scaled = value * ratio

    # Format nicely
    if scaled == int(scaled):
        return f"{int(scaled)} {rest}".strip()
    else:
        return f"{scaled:.1f} {rest}".strip()
