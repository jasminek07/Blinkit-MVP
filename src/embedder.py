import numpy as np
import re

class Embedder:
    def __init__(self, use_local_model=True):
        self.dimension = 384
        self.model = None
        self.mode = "hashing"

        if use_local_model:
            try:
                from sentence_transformers import SentenceTransformer
                print("Attempting to load sentence-transformers model 'BAAI/bge-small-en-v1.5'...")
                # Use a small local cache folder in the workspace to avoid permission issues
                self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
                self.mode = "sentence-transformers"
                print("Successfully loaded SentenceTransformer.")
            except Exception as e:
                print(f"Failed to load sentence-transformers ({e}). Falling back to deterministic Hashing Vectorizer.")

    def get_embedding(self, text):
        if self.mode == "sentence-transformers" and self.model is not None:
            try:
                # bge-small-en-v1.5 has 384 dimensions
                emb = self.model.encode(text, normalize_embeddings=True)
                return emb.tolist()
            except Exception as e:
                print(f"Error encoding with SentenceTransformer ({e}). Using Hashing Vectorizer fallback.")

        # Fallback Hashing Vectorizer (384 dimensions, normalized)
        # Tokenize and clean text
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        if not words:
            return [0.0] * self.dimension

        vector = np.zeros(self.dimension)
        for word in words:
            # Hash word into multiple dimensions to prevent collisions
            for seed in [13, 37, 73]:
                idx = hash(f"{seed}_{word}") % self.dimension
                # Use a sign hash for standard MurmurHash-like property
                sign = 1 if hash(f"sign_{seed}_{word}") % 2 == 0 else -1
                vector[idx] += sign

        # Normalize the vector to unit length (L2 norm)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def get_similarity(self, vec1, vec2):
        # Cosine similarity between two unit vectors is their dot product
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

if __name__ == "__main__":
    # Test embedder
    embedder = Embedder(use_local_model=False) # Test with hashing fallback first
    
    t1 = "The cable is very fast and durable. Highly recommend for quick charge."
    t2 = "Got it delivered in 10 mins! Highly recommend for quick charge. The cable is very fast and durable."
    t3 = "bahut badhiya sunscreen hai. Skin pe chipchipa nahi lagta."

    v1 = embedder.get_embedding(t1)
    v2 = embedder.get_embedding(t2)
    v3 = embedder.get_embedding(t3)

    print(f"Embedding dimensions: {len(v1)}")
    print(f"Similarity (t1 vs t2 - near duplicate): {embedder.get_similarity(v1, v2):.4f}")
    print(f"Similarity (t1 vs t3 - completely different): {embedder.get_similarity(v1, v3):.4f}")
