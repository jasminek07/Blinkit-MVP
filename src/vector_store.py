import os
import json
import numpy as np
from src.embedder import Embedder

class VectorStore:
    def __init__(self, persist_directory="data/chroma_db", use_local_model=False):
        self.persist_directory = persist_directory
        self.embedder = Embedder(use_local_model=use_local_model)
        self.mode = "chromadb"
        self.client = None
        self.collection = None
        
        # Local fallback store variables
        self.fallback_file = "data/fallback_vector_store.json"
        self.fallback_data = [] # List of dicts: {"id": id, "document": doc, "metadata": meta, "embedding": emb}
        
        # Local Query Cache
        self.query_cache = {}

        # Attempt to load ChromaDB
        try:
            import chromadb
            from chromadb.config import Settings
            print("Attempting to initialize ChromaDB...")
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name="blinkit_reviews",
                metadata={"hnsw:space": "cosine"}
            )
            print("Successfully initialized ChromaDB collection.")
        except Exception as e:
            print(f"Failed to initialize ChromaDB ({e}). Falling back to pure-Python/JSON vector store.")
            self.mode = "fallback"
            self._load_fallback_store()

    def _load_fallback_store(self):
        if os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, 'r', encoding='utf-8') as f:
                    self.fallback_data = json.load(f)
                print(f"Loaded {len(self.fallback_data)} records from fallback vector store.")
            except Exception as e:
                print(f"Error loading fallback store file: {e}")
                self.fallback_data = []
        else:
            self.fallback_data = []

    def _save_fallback_store(self):
        os.makedirs(os.path.dirname(self.fallback_file), exist_ok=True)
        try:
            with open(self.fallback_file, 'w', encoding='utf-8') as f:
                json.dump(self.fallback_data, f, indent=2)
            print(f"Saved fallback store to {self.fallback_file}")
        except Exception as e:
            print(f"Error saving fallback store file: {e}")

    def add_documents(self, documents, metadatas, ids):
        # Generate embeddings
        embeddings = [self.embedder.get_embedding(doc) for doc in documents]

        if self.mode == "chromadb" and self.collection is not None:
            try:
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Added {len(documents)} documents to ChromaDB.")
                return True
            except Exception as e:
                print(f"Error adding to ChromaDB: {e}. Switching to fallback mode.")
                self.mode = "fallback"
                self._load_fallback_store()

        # Fallback Mode Addition
        for doc, meta, id_val, emb in zip(documents, metadatas, ids, embeddings):
            # Check if ID already exists and overwrite, else append
            existing_idx = next((i for i, x in enumerate(self.fallback_data) if x["id"] == id_val), None)
            record = {
                "id": id_val,
                "document": doc,
                "metadata": meta,
                "embedding": emb
            }
            if existing_idx is not None:
                self.fallback_data[existing_idx] = record
            else:
                self.fallback_data.append(record)

        self._save_fallback_store()
        print(f"Added {len(documents)} documents to Fallback Vector Store.")
        return True

    def query(self, query_text, n_results=5, sku_filter=None):
        # Check Cache
        cache_key = (query_text, n_results, sku_filter)
        if cache_key in self.query_cache:
            print("Returning cached vector search results.")
            return self.query_cache[cache_key]

        query_vector = self.embedder.get_embedding(query_text)

        if self.mode == "chromadb" and self.collection is not None:
            try:
                # Prepare filter
                where_filter = None
                if sku_filter:
                    where_filter = {"sku_id": sku_filter}
                
                results = self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=n_results,
                    where=where_filter
                )
                
                # Format output consistently
                formatted_results = {
                    "documents": results["documents"][0] if results["documents"] else [],
                    "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                    "distances": results["distances"][0] if results["distances"] else [],
                    "ids": results["ids"][0] if results["ids"] else []
                }
                self.query_cache[cache_key] = formatted_results
                return formatted_results
            except Exception as e:
                print(f"ChromaDB query error: {e}. Attempting fallback query.")
                self.mode = "fallback"
                self._load_fallback_store()

        # Fallback Mode Query
        # 1. Filter by SKU first if filter is provided
        candidates = self.fallback_data
        if sku_filter:
            candidates = [c for c in self.fallback_data if c["metadata"].get("sku_id") == sku_filter]

        if not candidates:
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}

        # 2. Compute similarity for each candidate
        scored_candidates = []
        for c in candidates:
            sim = self.embedder.get_similarity(query_vector, c["embedding"])
            # Distance is 1.0 - Cosine Similarity
            distance = 1.0 - sim
            scored_candidates.append((distance, c))

        # 3. Sort by distance (ascending)
        scored_candidates.sort(key=lambda x: x[0])

        # 4. Limit results
        top_results = scored_candidates[:n_results]

        # 5. Format output
        formatted_results = {
            "documents": [c["document"] for _, c in top_results],
            "metadatas": [c["metadata"] for _, c in top_results],
            "distances": [dist for dist, _ in top_results],
            "ids": [c["id"] for _, c in top_results]
        }
        
        # Save to Cache
        self.query_cache[cache_key] = formatted_results
        return formatted_results

if __name__ == "__main__":
    # Test vector store in fallback mode
    store = VectorStore(persist_directory="data/chroma_db_test", use_local_model=False)
    
    docs = [
        "This sunscreen is super light and non-greasy.",
        "Perfect sunscreen for hot summer days.",
        "This USB C cable is durable and support fast charging."
    ]
    metas = [
        {"sku_id": "SKU-SUNSCREEN", "category": "Beauty/Skincare"},
        {"sku_id": "SKU-SUNSCREEN", "category": "Beauty/Skincare"},
        {"sku_id": "SKU-CABLE", "category": "Electronics"}
    ]
    ids = ["doc1", "doc2", "doc3"]

    store.add_documents(docs, metas, ids)

    # Search for sunscreen
    res = store.query("light sunscreen", n_results=2, sku_filter="SKU-SUNSCREEN")
    print("\nSunscreen Search Results:")
    for doc, dist, meta in zip(res["documents"], res["distances"], res["metadatas"]):
        similarity = 1.0 - dist
        print(f"Doc: '{doc}', Sim: {similarity:.4f}, Meta: {meta}")

    # Search for cable
    res_cable = store.query("charger cable", n_results=1, sku_filter="SKU-CABLE")
    print("\nCable Search Results:")
    for doc, dist, meta in zip(res_cable["documents"], res_cable["distances"], res_cable["metadatas"]):
        similarity = 1.0 - dist
        print(f"Doc: '{doc}', Sim: {similarity:.4f}, Meta: {meta}")
