# RecipeLens - Indian Recipe Scraper & Browser

**RecipeLens** is a full-stack application for scraping, searching, browsing, and scaling Indian recipes. It fetches recipes from [tarladalal.com](https://www.tarladalal.com), extracts ingredients, time fields, tags, and nutritional information, and provides a modern web interface for exploration.

---

## 📋 Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Running the Application](#running-the-application)
6. [Usage](#usage)
7. [Available Scripts](#available-scripts)
8. [API Endpoints](#api-endpoints)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)

---

## 📁 Project Structure

```
scrap_recipes/
├── scrap_recipes.py          # Main scraper script
├── extract_ingredients.py    # Ingredient extraction from DB
├── requirements.txt          # Python dependencies
├── requirements copy.txt     # Alternative requirements
├── load_json_2es.py          # Load data to Elasticsearch
├── test_llm.py               # LLM testing script
├── refresh_embeddings.bat    # Refresh embeddings batch file
├── refresh_embeddings.py     # Refresh embeddings script
├── test_rag.py               # RAG testing script
├── mock_test.py              # Mock test script
├── backend/
│   ├── __init__.py
│   ├── database.py           # SQLite schema & queries
│   ├── main.py               # FastAPI application
│   ├── ollama_client.py      # Ollama API client
│   ├── import_data.py        # Import data from CSV/JSON
│   └── recipe_embeddings.json
├── elk/
│   └── search_recipe_by_ingredient.py
├── frontend/
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite config
│   ├── eslint.config.js      # ESLint config
│   ├── index.html
│   ├── README.md
│   ├── src/
│   │   ├── main.jsx          # React entry point
│   │   ├── App.jsx           # Root component
│   │   ├── theme.js          # Chakra UI theme
│   │   ├── api/
│   │   │   └── client.js     # API client
│   │   ├── components/
│   │   │   ├── RecipeCard.jsx
│   │   │   ├── ScalingPanel.jsx
│   │   │   ├── SearchFilters.jsx
│   │   │   └── NutrientBadges.jsx
│   │   ├── pages/
│   │ │   ├── SearchPage.jsx
│   │ │   ├── RecipePage.jsx
│   │ │   ├── AdminPage.jsx
│   │ │   └── CaloriesPage.jsx
│   │   └── pages/
│   │       ├── App.css
│   │       ├── App.jsx
│   │       ├── index.css
│   │       └── main.jsx
│   └── public/
│       └── ...
├── scripts/
│   ├── populate_calories.py
│   └── refresh_embeddings.py
├── recipe_all.csv / recipe_all.json
├── recipes_all_from_p1_20260214_1050.csv
├── recipes_universal_all_20260215_1053.csv / .json
├── recipes_universal_limit2_20260215_1026.csv / .json
├── allrecipes_2es.conf
├── ingredient_analysis.txt
├── start_app.bat             # Launches both backend & frontend
└── README.md                 # This file
```

---

## 🛠️ Prerequisites

### Python (Backend)

- Python 3.9+ recommended
- [pip](https://pip.pypa.io/en/stable/installation/) installed

**Required Python packages** (see `requirements.txt`):
- `beautifulsoup4` / `bs4`
- `cloudscraper`
- `pandas`
- `fastapi`
- `uvicorn`
- `httpx`
- `aiosqlite`
- `elasticsearch` (for `load_json_2es.py`)
- `nltk`, `textblob`, `textblob-core`
- `tqdm`

### Node.js (Frontend)

- [Node.js](https://nodejs.org/) (v18+ recommended) with npm

**Required Node packages** (see `frontend/package.json`):
- `react`, `react-dom`
- `vite`
- `@chakra-ui/react`, `@chakra-ui/icons`
- `@emotion/react`, `@emotion/styled`
- `axios`, `framer-motion`
- `react-router-dom`, `react-markdown`

---

## 🐍 Backend Setup

### 1. Create a virtual environment (recommended)

```powershell
cd c:\Users\amankar\Documents\mylearning\lpython\scrap_recipes
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 3. Verify Ollama is available (for AI features)

The application uses [Ollama](https://ollama.ai/) for AI summarization and recipe scaling. Make sure Ollama is running on your machine with a compatible model loaded.

```powershell
# Check Ollama is running
ollama list

# Pull a model if needed
ollama pull lfm2.5-thinking:latest
```

### 4. Database initialization

The SQLite database (`backend/recipes.db`) is automatically created on first startup via FastAPI's lifespan event. No manual setup required.

---

## ⚡ Frontend Setup

### 1. Install Node dependencies

```powershell
cd c:\Users\amankar\Documents\mylearning\lpython\scrap_recipes\frontend
npm install
```

### 2. Verify API connection

The frontend connects to the backend at `http://localhost:8000/api`. Ensure the backend is running before starting the frontend.

---

## ▶️ Running the Application

### Option 1: Using `start_app.bat` (Recommended)

The easiest way to start everything is via the provided batch file:

```powershell
cd c:\Users\amankar\Documents\mylearning\lpython\scrap_recipes
start_app.bat
```

This will:
1. Stop any existing Python/Node processes
2. Launch the backend (FastAPI on `http://localhost:8000`)
3. Launch the frontend (Vite dev server on `http://localhost:5173`)
4. Open the browser to `http://localhost:5173`

### Option 2: Manual Start

#### Start the Backend

```powershell
cd c:\Users\amankar\Documents\mylearning\lpython\scrap_recipes
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Start the Frontend

```powershell
cd c:\Users\amankar\Documents\mylearning\lpython\scrap_recipes\frontend
npm run dev
```

#### Open Browser

Navigate to `http://localhost:5173`

---

## 📖 usage

### Homepage / Search Page

- Browse recipes by searching names, ingredients, tags, or categories
- Filter by calories range, tags, and categories
- Pagination available for large result sets

### Recipe Detail Page

Click any recipe to view:
- **Details tab**: Ingredients, preparation/cooking/baking times, makes, tags
- **AI Summary tab**: AI-generated summary via Ollama
- **Scale tab**: Scale ingredients to different serving sizes

### Scaling Panel

- Enter target servings (1-100)
- Choose mode: `llm` (uses Ollama LLM) or `algorithmic` (math-based proportion)
- Click "Scale Recipe" to get adjusted ingredient quantities

### Calories Page

- Search for ingredient calorie information
- View original names, quantities, and categories
- Pagination for large result sets

### Admin Page (requires Ollama)

- List available Ollama models
- Set active model/embedding model
- Refresh vector embeddings
- View/change application settings

---

## 📦 Available Scripts

### Backend Scripts

| Script | Description |
|--------|-------------|
| `scrap_recipes.py` | Main web scraper - fetches recipes from tarladalal.com categories |
| `extract_ingredients.py` | Extracts and analyzes ingredient frequencies from the database |
| `load_json_2es.py` | Loads recipe data into Elasticsearch |
| `refresh_embeddings.py` | Refreshes vector embeddings via Ollama |
| `test_llm.py` | Tests Ollama connection and model availability |
| `mock_test.py` | Mock/test script for development |

### Frontend Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start Vite development server |
| `npm run build` | Build production bundle |
| `npm run lint` | Run ESLint |
| `npm run preview` | Preview production build |

### Batch Files

| File | Description |
|------|-------------|
| `start_app.bat` | Launches both backend and frontend |
| `refresh_embeddings.bat` | Refreshes embeddings (calls Python script) |

---

## 🔌 API Endpoints

### Backend (FastAPI) - `http://localhost:8000/api`

#### Recipe Search

- `GET /recipes/search` - Search recipes with filters (query, ingredient, tags, category, calories)
- `GET /recipes/{id}` - Get recipe by ID
- `GET /recipes/` - List all recipes (paginated)

#### Ingredient Search

- `GET /ingredients/search` - Search ingredient calorie details

#### Ollama Operations

- `POST /recipes/{id}/summarize` - AI summarize a recipe
- `POST /recipes/{id}/scale` - Scale recipe ingredients
- `GET /admin/models` - List Ollama models
- `POST /admin/model` - Set active model
- `POST /admin/embedding-model` - Set embedding model
- `POST /admin/refresh-embeddings` - Refresh embeddings
- `GET /admin/refresh-status` - Check refresh status
- `GET /admin/settings` - Get application settings

#### Utility

- `GET /tags` - List all tags
- `GET /categories` - List all categories

---

## ⚙️ Configuration

### Environment Variables

No `.env` file is required - the application uses sensible defaults:

- **Backend API URL**: `http://localhost:8000` (in `frontend/src/api/client.js`)
- **Ollama Base URL**: `http://localhost:11435` (in `backend/ollama_client.py`)
- **Database Path**: `backend/recipes.db` (relative to project root)

### Customizing Scraping

Edit `scrap_recipes.py` to modify:
- `CATEGORY_LISTING_URL` - Base category URL
- Page range (`start_page`, `end_page`)
- `scrape_all` mode for unlimited scraping
- Recipe URL filtering (`url2skip`)

### Adjusting Ollama Settings

In the Admin Page or via API:
- Set active model: `POST /admin/model { "model": "your-model-name" }`
- Set embedding model: `POST /admin/embedding-model { "model": "nomic-embed-text" }`

---

## 🛠️ Troubleshooting

### Common Issues

1. **Ollama not running**
   - Start Ollama: `ollama serve`
   - Pull a model: `ollama pull lfm2.5-thinking:latest`

2. **Backend won't start**
   - Ensure virtual environment is activated
   - Check `requirements.txt` packages are installed
   - Verify no port conflicts (8000, 5173)

3. **Frontend can't connect to backend**
   - Ensure backend is running on port 8000
   - Check CORS settings in `backend/main.py` (currently allows `*`)

4. **Scraping errors**
   - Website structure may have changed
   - Check `scrap_recipes.py` for updated HTML selectors
   - Some categories may have different page structures

5. **Database locked errors**
   - Close other connections to `recipes.db`
   - The app uses `aiosqlite` for async access

### Debug Mode

Run with `--reload` flag for auto-reload on code changes:
```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📄 License

This project is for personal/educational use. Recipe data scraped from [tarladalal.com](https://www.tarladalal.com) is subject to their terms of service.

---

## 🙏 Acknowledgments

- Recipe data sourced from [tarladalal.com](https://www.tarladalal.com)
- UI built with [Chakra UI](https://chakra-ui.com/)
- FastAPI for the backend API
- Ollama for local LLM inference
- Vite for the frontend build tooling
