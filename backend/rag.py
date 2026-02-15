import os
import asyncio
import numpy as np
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from backend.ollama_client import get_embedding

CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

class RAGSystem:
    def __init__(self):
        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        
        # Create or get collection with cosine similarity space
        self.collection = self.client.get_or_create_collection(
            name="recipes",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.indexing_status = {
            "is_indexing": False,
            "processed": 0,
            "total": 0,
            "message": "Idle"
        }
        
        # We don't need to load all embeddings into memory anymore!
        # Just check count
        count = self.collection.count()
        print(f"RAG initialized. Collection has {count} documents.")

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
        
        # Clear existing collection to ensure fresh start (optional, but good for "Refresh")
        # In a real system we might upsert diffs, but "Refresh" implies rebuilt.
        # Faster to delete and recreate usage?
        # self.client.delete_collection("recipes")
        # self.collection = self.client.create_collection(...)
        # But for now, we'll just upsert and maybe checking for deletions is too complex for this step.
        # Let's just upsert. If user wants full clear, we can add a flag later.
        # Actually, if recipes were deleted from DB, they remain in Chroma. 
        # For a clean "Refresh", let's clear it.
        try:
            print("Clearing existing collection...")
            self.client.delete_collection("recipes")
            self.collection = self.client.get_or_create_collection(
                name="recipes",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Error resetting collection: {e}")

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
                        return {
                            "id": str(recipe['id']),
                            "embedding": embedding,
                            "metadata": {
                                "name": recipe['name'],
                                "url": recipe['url']
                            },
                            "document": text
                        }
                except Exception as e:
                    print(f"Failed to embed recipe {recipe['id']}: {e}")
            return None

        print(f"Indexing {len(recipes)} recipes with parallelism...")
        
        batch_size = 50
        total = len(recipes)
        
        try:
            for i in range(0, total, batch_size):
                batch = recipes[i : i + batch_size]
                
                # 1. Generate embeddings in parallel
                tasks = [process_recipe(r) for r in batch]
                results = await asyncio.gather(*tasks)
                
                # 2. Prepare batch for Chroma
                ids = []
                embeddings = []
                metadatas = []
                documents = []
                
                for res in results:
                    if res:
                        ids.append(res["id"])
                        embeddings.append(res["embedding"])
                        metadatas.append(res["metadata"])
                        documents.append(res["document"])
                
                if ids:
                    # 3. Insert into Chroma (offload to thread as it can be blocking)
                    await asyncio.to_thread(
                        self.collection.upsert,
                        ids=ids,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        documents=documents
                    )
                
                processed_count = min(i + batch_size, total)
                self.indexing_status["processed"] = processed_count
                self.indexing_status["message"] = f"Processed {processed_count}/{total}"
                print(f"Processed {processed_count}/{total}")

            self.indexing_status["message"] = "Completed"
            return self.collection.count()
            
        except Exception as e:
            self.indexing_status["message"] = f"Failed: {str(e)}"
            print(f"Indexing failed: {e}")
            return 0
        finally:
            self.indexing_status["is_indexing"] = False

    def reload_embeddings(self):
        """No-op for ChromaDB as it is persistent."""
        pass

    @property
    def vectors(self):
        """Mock property for backward compatibility check in main.py"""
        if self.collection.count() > 0:
            return [1] # Just truthy
        return None
        
    @property
    def ids(self):
        """Mock property for backward compatibility"""
        # We shouldn't access this directly usually, but logging uses it
        return [f"count: {self.collection.count()}"]

    async def search(self, query: str, top_k: int = 100) -> List[int]:
        """Search for recipes semantically similar to query. Returns list of recipe IDs."""
        try:
            query = query.strip()
            
            # 1. Embed query
            query_embedding = await get_embedding(query)
            if not query_embedding:
                print("Failed to get query embedding")
                return []
            
            # 2. Query Chroma (offload to thread)
            results = await asyncio.to_thread(
                self.collection.query,
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["distances", "metadatas"] 
            )
            
            # results is dict: {'ids': [['id1', ...]], 'distances': [[0.1, ...]], ...}
            if not results['ids'] or not results['ids'][0]:
                return []
                
            found_ids = results['ids'][0]
            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            
            scored_results = []
            
            query_lower = query.lower()
            
            for r_id, dist, meta in zip(found_ids, distances, metadatas):
                # Apply Keyword Boosting
                # If the query (or parts of it) appears in the title, boost the score (reduce distance)
                # This helps "Pulao" find "Vegetable Pulao" even if vector similarity is weak.
                
                final_dist = dist
                name_lower = meta.get('name', '').lower()
                
                # Check for full query in name
                if query_lower in name_lower:
                    final_dist -= 0.20  # Significant boost
                else:
                    # Check for partial word matches (e.g. "Chicken" in "Chicken Curry")
                    query_words = query_lower.split()
                    matches = sum(1 for w in query_words if len(w) > 3 and w in name_lower)
                    if matches > 0:
                        final_dist -= (0.05 * matches)

                # Relaxed threshold from 0.55 to 0.60 to happen after boosting
                # If boosted, a 0.7 distance might become 0.5 and pass.
                if final_dist < 0.60:
                    scored_results.append((final_dist, int(r_id)))
            
            # Sort by new distance
            scored_results.sort(key=lambda x: x[0])
            
            return [x[1] for x in scored_results]
            
        except Exception as e:
            print(f"RAG Search failed: {e}")
            return []

rag_system = RAGSystem()
