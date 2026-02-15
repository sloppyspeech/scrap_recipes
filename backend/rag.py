import json
import os
import asyncio
import numpy as np
from typing import List, Dict, Any
from backend.ollama_client import get_embedding, OLLAMA_BASE_URL
import httpx

EMBEDDINGS_FILE = os.path.join(os.path.dirname(__file__), "recipe_embeddings.json")

class RAGSystem:
    def __init__(self):
        self.embeddings = {}
        self.vectors = None
        self.ids = []
        self.indexing_status = {
            "is_indexing": False,
            "processed": 0,
            "total": 0,
            "message": "Idle"
        }
        self._load_embeddings()

    def _load_embeddings(self):
        """Load embeddings from disk into memory."""
        if os.path.exists(EMBEDDINGS_FILE):
            try:
                with open(EMBEDDINGS_FILE, "r") as f:
                    self.embeddings = json.load(f)
                
                # Pre-convert to numpy array for fast cosine similarity
                if self.embeddings:
                    self.ids = list(self.embeddings.keys())
                    # Convert list of lists to numpy array
                    self.vectors = np.array([self.embeddings[id] for id in self.ids], dtype=np.float32)
                    
                    # Normalize vectors for cosine similarity (dot product of normalized vectors)
                    norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
                    # Avoid division by zero
                    norms[norms == 0] = 1
                    self.vectors = self.vectors / norms
                    
                print(f"Loaded {len(self.embeddings)} recipe embeddings.")
            except Exception as e:
                print(f"Failed to load embeddings: {e}")
                self.embeddings = {}
        else:
            print("No embeddings file found. RAG search will not work until indexed.")

    async def index_recipes(self, recipes: List[Dict[str, Any]]):
        if self.indexing_status["is_indexing"]:
            print("Indexing already in progress")
            return 0
            
        self.indexing_status = {
            "is_indexing": True,
            "processed": 0,
            "total": len(recipes),
            "message": "Starting indexing..."
        }
        
        new_embeddings = {}
        semaphore = asyncio.Semaphore(5)  # Limit concurrency to avoid overloading Ollama

        async def process_recipe(recipe):
            text = f"{recipe['name']}. Ingredients: "
            text += ", ".join([ing['name'] for ing in recipe.get('ingredients', [])])
            if recipe.get('tags'):
                text += f". Tags: {', '.join(recipe.get('tags', []))}"
            
            async with semaphore:
                try:
                    embedding = await get_embedding(text)
                    if embedding:
                        return str(recipe['id']), embedding
                except Exception as e:
                    print(f"Failed to embed recipe {recipe['id']}: {e}")
            return None

        print(f"Indexing {len(recipes)} recipes with parallelism...")
        
        # Process in batches to show progress
        batch_size = 50
        total = len(recipes)
        
        try:
            for i in range(0, total, batch_size):
                batch = recipes[i : i + batch_size]
                tasks = [process_recipe(r) for r in batch]
                results = await asyncio.gather(*tasks)
                
                for res in results:
                    if res:
                        r_id, emb = res
                        new_embeddings[r_id] = emb
                
                processed_count = min(i + batch_size, total)
                self.indexing_status["processed"] = processed_count
                self.indexing_status["message"] = f"Processed {processed_count}/{total}"
                print(f"Processed {processed_count}/{total}")

            # Save to disk
            print("Saving embeddings to disk...")
            self.indexing_status["message"] = "Saving to disk..."
            with open(EMBEDDINGS_FILE, "w") as f:
                json.dump(new_embeddings, f)
                
            # Reload
            self._load_embeddings()
            
            self.indexing_status["message"] = "Completed"
            return len(new_embeddings)
            
        except Exception as e:
            self.indexing_status["message"] = f"Failed: {str(e)}"
            print(f"Indexing failed: {e}")
            return 0
        finally:
            self.indexing_status["is_indexing"] = False

    def reload_embeddings(self):
        """Force reload of embeddings from disk"""
        self._load_embeddings()

    async def search(self, query: str, top_k: int = 100) -> List[int]:
        """Search for recipes semantically similar to query. Returns list of recipe IDs."""
        if self.vectors is None or len(self.vectors) == 0:
            return []

        try:
            # 1. Embed query
            query_embedding = await get_embedding(query)
            if not query_embedding:
                print("Failed to get query embedding")
                return []
            
            q_vec = np.array(query_embedding, dtype=np.float32)
            q_norm = np.linalg.norm(q_vec)
            if q_norm == 0:
                return []
            q_vec = q_vec / q_norm

            # 2. Cosine Similarity
            # (N, D) dot (D,) -> (N,)
            scores = np.dot(self.vectors, q_vec)
            
            # 3. Get top K
            # argsort returns indices of sorted array (ascending by default)
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                score = scores[idx]
                recipe_id = int(self.ids[idx])
                # Filter out low relevance if needed, e.g. score > 0.45
                if score > 0.45:
                    results.append(recipe_id)
            
            return results
            
        except Exception as e:
            print(f"RAG Search failed: {e}")
            return []

rag_system = RAGSystem()
