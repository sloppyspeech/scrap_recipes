"""
FastAPI application for the Recipe UI.
Provides search, recipe details, Ollama-powered summarization/scaling, and admin endpoints.
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx

from backend.database import init_db, search_recipes, get_recipe_by_id, get_all_tags, get_all_categories
from backend.ollama_client import (
    summarize_recipe, scale_with_llm, scale_algorithmically,
    list_models, get_active_model, set_active_model, extract_search_filters,
    get_active_embedding_model, set_active_embedding_model,
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


class NaturalSearchRequest(BaseModel):
    query: str


# ─── Search Endpoints ──────────────────────────────────────────────

@app.get("/api/recipes/search")
async def api_search_recipes(
    q: str = Query("", description="Recipe name search"),
    ingredient: str = Query(None, description="Legacy ingredient filter"),
    include_ingredients: list[str] = Query(None, description="Ingredients to include"),
    exclude_ingredients: list[str] = Query(None, description="Ingredients to exclude"),
    tag: str = Query("", description="Tag filter (comma separated)"),
    category: str = Query("", description="Category filter"),
    cal_min: float = Query(None, description="Minimum calories"),
    cal_max: float = Query(None, description="Maximum calories"),
    nutrient: str = Query("", description="Nutrient field name (e.g. proteinContent)"),
    nutrient_max: float = Query(None, description="Max value for nutrient filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Search recipes with multiple filters."""
    # Merge legacy ingredient param into include_ingredients
    incl = include_ingredients or []
    if ingredient and ingredient not in incl:
        incl.append(ingredient)

    # Parse tags from comma-separated string
    tag_list = []
    if tag:
        tag_list = [t.strip() for t in tag.split(',') if t.strip()]

    result = await search_recipes(
        q=q,
        include_ingredients=incl,
        exclude_ingredients=exclude_ingredients,
        tags=tag_list,
        category=category,
        cal_min=cal_min, cal_max=cal_max,
        nutrient=nutrient, nutrient_max=nutrient_max,
        page=page, page_size=page_size,
    )
    return result



from backend.rag import rag_system

class NaturalSearchRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 20

@app.post("/api/recipes/search/natural")
async def api_search_natural(req: NaturalSearchRequest):
    """
    Perform RAG-based search:
    1. Retrieve relevant recipes using vector search.
    2. Generate a natural language answer using LLM with retrieved recipes as context.
    """
    # 1. Retrieval
    # Hybrid Approach: Vector Search + Keyword Search
    
    # A. Vector Search (Semantic) - Top 50 as requested
    limit_vector = 50
    vector_ids = await rag_system.search(req.query, top_k=limit_vector)
    
    # B. Keyword Search (Exact/Partial Match)
    from backend.database import search_recipes
    # Fetch a larger pool of keyword matches to ensure we cover "Pulao" cases
    keyword_result = await search_recipes(q=req.query, page_size=200) 
    keyword_recipes = keyword_result.get("recipes", [])
    keyword_ids = [r['id'] for r in keyword_recipes]
    
    # C. Merge (Keyword prioritized, then append unique Vector)
    # Use a dict to preserve order and uniqueness (Simulating an Ordered Set)
    merged_map = {}
    
    # Add keyword results FIRST (Classic Search Priority)
    for rid in keyword_ids:
        merged_map[rid] = True
        
    # Add vector results if not present (AI Discovery)
    for rid in vector_ids:
        if rid not in merged_map:
            merged_map[rid] = True
            
    all_recipe_ids = list(merged_map.keys())
    
    # Calculate pagination slices
    total_found = len(all_recipe_ids)
    start_idx = (req.page - 1) * req.page_size
    end_idx = start_idx + req.page_size
    
    # Slice IDs for the current page
    paged_recipe_ids = all_recipe_ids[start_idx:end_idx]
    
    # Fetch full details for the PAGE results
    paged_recipes = []
    # Optimization: if we already have recipe details from keyword search, use them?
    # But vector results didn't fetch details yet. 
    # To keep it simple and consistent: fetch by ID. 
    # (Optional optimization: use keyword_recipes lookup if available)
    
    keyword_lookup = {r['id']: r for r in keyword_recipes}
    
    for r_id in paged_recipe_ids:
        if r_id in keyword_lookup:
            paged_recipes.append(keyword_lookup[r_id])
        else:
            r = await get_recipe_by_id(r_id)
            if r:
                paged_recipes.append(r)
            
    if not all_recipe_ids:
        return {
            "results": {"recipes": [], "total": 0, "page": req.page, "page_size": req.page_size},
            "answer": "I couldn't find any recipes matching your description."
        }

    # 2. Generation (Answer)
    # Use top 5 results for context regardless of pagination
    # Note: These top 5 come from the MERGED list.
    context_ids = all_recipe_ids[:5]
    context_recipes = []
    
    # We need full details (especially ingredients) for the context.
    # paged_recipes might contain some, but not necessarily the top 5 if page > 1.
    # Also, keyword search results (if used) might NOT have ingredients populate if search_recipes doesn't return them.
    # search_recipes returns: id, name, url, makes, calories, time. NO INGREDIENTS.
    
    # So we must insure we have full details.
    
    for r_id in context_ids:
        # Check if we already have it in paged_recipes (optimization)
        found_r = None
        for r in paged_recipes:
             if r['id'] == r_id:
                 found_r = r
                 break
        
        # Even if found, does it have ingredients?
        if found_r and 'ingredients' in found_r:
            context_recipes.append(found_r)
        else:
            # Need to fetch full
            full_r = await get_recipe_by_id(r_id)
            if full_r:
                context_recipes.append(full_r)

    # Construct context from top recipes
    context_parts = []
    for r in context_recipes:
        # Format ingredients list
        # Check safety again just in case
        ing_list = r.get('ingredients', [])
        ings = ", ".join([f"{i.get('quantity', '')} {i['name']}".strip() for i in ing_list[:8]])
        if len(ing_list) > 8:
            ings += "..."
            
        context_parts.append(
            f"Recipe: {r['name']}\n"
            f"Description: A {r.get('makes', '')} dish. "
            f"Time: {r.get('times', {}).get('total_time', 'N/A')}. "
            f"Calories: {r.get('calories', 'N/A')}. "
            f"Ingredients: {ings}"
        )
    
    context_str = "\n\n".join(context_parts)

    # Use the active model to generate answer
    from backend.ollama_client import chat_completion
    prompt = f"""
You are a helpful culinary assistant.
Answer the user's query based ONLY on the following recipes.
If the recipes aren't relevant, say so, but suggest the best option from the list.
Do not invent recipes.

User Query: {req.query}

Context Recipes:
{context_str}

Answer:
    """
    
    try:
        answer = await chat_completion(prompt)
    except Exception as e:
        answer = "I found some recipes but couldn't generate an answer."
        print(f"Generation failed: {e}")

    # Return standard search result structure + the answer
    return {
        "results": {
            "recipes": paged_recipes,
            "total": total_found,
            "page": req.page,
            "page_size": req.page_size
        },
        "answer": answer
    }


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


@app.get("/api/categories")
async def api_get_categories():
    """List all categories with recipe counts."""
    return await get_all_categories()


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
    return {
        "models": models, 
        "active_model": get_active_model(),
        "active_embedding_model": get_active_embedding_model()
    }


@app.post("/api/admin/model")
async def api_set_model(req: ModelRequest):
    """Set the active Ollama model."""
    set_active_model(req.model)
    return {"status": "success", "active_model": get_active_model()}


@app.post("/api/admin/embedding-model")
async def api_set_embedding_model(req: ModelRequest):
    """Set the active Embedding model."""
    set_active_embedding_model(req.model)
    return {"status": "success", "active_embedding_model": get_active_embedding_model()}


@app.post("/api/admin/refresh-embeddings")
async def api_refresh_embeddings(background_tasks: BackgroundTasks):
    """Trigger background re-indexing of all recipes."""
    if rag_system.indexing_status["is_indexing"]:
        return {"status": "error", "message": "Indexing already in progress"}
    
    # Fetch all recipes to index
    # We need to import get_all_recipes inside or ensure it's imported at top
    from backend.database import get_all_recipes
    all_recipes = await get_all_recipes()
    
    # Run in background
    background_tasks.add_task(rag_system.index_recipes, all_recipes)
    
    return {"status": "success", "message": "Indexing started in background"}


@app.get("/api/admin/refresh-status")
async def api_refresh_status():
    """Get current indexing status."""
    return rag_system.indexing_status


@app.get("/api/admin/settings")
async def api_get_settings():
    """Get current admin settings."""
    return {
        "active_model": get_active_model(),
        "active_embedding_model": get_active_embedding_model(),
        "ollama_url": OLLAMA_BASE_URL,
        "rag_status": "loaded" if rag_system.vectors is not None else "empty"
    }


@app.post("/api/system/reload-index")
async def api_reload_index():
    """Force reload of the RAG index from disk."""
    try:
        rag_system.reload_embeddings()
        return {"status": "success", "message": f"Index reloaded. Loaded {len(rag_system.ids)} vectors."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
