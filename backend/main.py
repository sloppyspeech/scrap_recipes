"""
FastAPI application for the Recipe UI.
Provides search, recipe details, Ollama-powered summarization/scaling, and admin endpoints.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx

from backend.database import init_db, search_recipes, get_recipe_by_id, get_all_tags
from backend.ollama_client import (
    summarize_recipe, scale_with_llm, scale_algorithmically,
    list_models, get_active_model, set_active_model,
    OLLAMA_BASE_URL
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Recipe Browser API",
    description="Search, browse, and scale Indian recipes with LLM integration",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Pydantic Models ───────────────────────────────────────────────

class ScaleRequest(BaseModel):
    target_servings: int
    mode: str = "llm"  # "llm" or "algorithmic"


class ModelRequest(BaseModel):
    model: str


# ─── Search Endpoints ──────────────────────────────────────────────

@app.get("/api/recipes/search")
async def api_search_recipes(
    q: str = Query("", description="Recipe name search"),
    ingredient: str = Query("", description="Ingredient name search"),
    tag: str = Query("", description="Tag filter"),
    cal_min: float = Query(None, description="Minimum calories"),
    cal_max: float = Query(None, description="Maximum calories"),
    nutrient: str = Query("", description="Nutrient field name (e.g. proteinContent)"),
    nutrient_max: float = Query(None, description="Max value for nutrient filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Search recipes with multiple filters."""
    result = await search_recipes(
        q=q, ingredient=ingredient, tag=tag,
        cal_min=cal_min, cal_max=cal_max,
        nutrient=nutrient, nutrient_max=nutrient_max,
        page=page, page_size=page_size,
    )
    return result


@app.get("/api/recipes/{recipe_id}")
async def api_get_recipe(recipe_id: int):
    """Get full recipe details by ID."""
    recipe = await get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.get("/api/tags")
async def api_get_tags():
    """List all tags with recipe counts."""
    return await get_all_tags()


# ─── Ollama Integration Endpoints ──────────────────────────────────

@app.post("/api/recipes/{recipe_id}/summarize")
async def api_summarize_recipe(recipe_id: int):
    """Fetch the recipe page and use Ollama to summarize it."""
    recipe = await get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    url = recipe["url"]

    # Fetch the recipe page using cloudscraper to bypass 403/Cloudflare
    try:
        import cloudscraper
        from fastapi.concurrency import run_in_threadpool
        
        def fetch_url(target_url):
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
            )
            return scraper.get(target_url)

        resp = await run_in_threadpool(fetch_url, url)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"External site returned {resp.status_code}")
            
        page_html = resp.text
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch recipe page: {str(e)}")

    # Extract text from HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page_html, "html.parser")
    # Remove script/style
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    page_text = soup.get_text(separator="\n", strip=True)

    # Summarize with Ollama
    try:
        summary = await summarize_recipe(page_text, recipe["name"])
        return {"summary": summary, "model": get_active_model()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama summarization failed: {e}")


@app.post("/api/recipes/{recipe_id}/scale")
async def api_scale_recipe(recipe_id: int, req: ScaleRequest):
    """Scale recipe ingredients for target servings."""
    recipe = await get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ingredients = recipe["ingredients"]
    original_servings = recipe.get("makes", "1 serving")

    if req.mode == "llm":
        try:
            scaled = await scale_with_llm(ingredients, original_servings, req.target_servings)
            return {
                "scaled_ingredients": scaled,
                "mode": "llm",
                "model": get_active_model(),
                "original_servings": original_servings,
                "target_servings": req.target_servings,
            }
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM scaling failed: {e}")
    else:
        scaled = scale_algorithmically(ingredients, original_servings, req.target_servings)
        return {
            "scaled_ingredients": scaled,
            "mode": "algorithmic",
            "original_servings": original_servings,
            "target_servings": req.target_servings,
        }


# ─── Admin Endpoints ───────────────────────────────────────────────

@app.get("/api/admin/models")
async def api_list_models():
    """List available Ollama models."""
    models = await list_models()
    return {"models": models, "active_model": get_active_model()}


@app.post("/api/admin/model")
async def api_set_model(req: ModelRequest):
    """Set the active Ollama model."""
    set_active_model(req.model)
    return {"active_model": get_active_model()}


@app.get("/api/admin/settings")
async def api_get_settings():
    """Get current admin settings."""
    return {
        "active_model": get_active_model(),
        "ollama_url": OLLAMA_BASE_URL,
    }
