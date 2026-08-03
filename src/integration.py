import sqlite3
import os
from src.vector_store import VectorStore

DB_PATH = "data/blinkit_local.db"

class IntegrationRouter:
    def __init__(self, use_local_model=False):
        # Initialize the vector store client
        self.vector_store = VectorStore(persist_directory="data/chroma_db", use_local_model=use_local_model)
        
        # Local Caches
        self.evidence_cache = {}
        self.recs_cache = {}

    def run_evidence_gate(self, sku_id, query_text=None, similarity_threshold=0.90):
        """
        Executes the Evidence Gate protocol:
        1. Query catalog for SKU name if query_text is not provided.
        2. Query ChromaDB for review records matching the target SKU.
        3. Filter reviews where similarity S >= similarity_threshold.
        4. If matching count < 2, trigger fallback_mode = True.
        """
        # Check Cache
        cache_key = (sku_id, query_text, similarity_threshold)
        if cache_key in self.evidence_cache:
            print("Returning cached Evidence Gate results.")
            return self.evidence_cache[cache_key]

        # Fetch SKU metadata from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, base_rating, review_count FROM sku_catalog WHERE sku_id = ?", (sku_id,))
        sku_row = cursor.fetchone()
        conn.close()

        if not sku_row:
            print(f"SKU {sku_id} not found in catalog. Triggering fallback.")
            return True, [], {"rating": 0.0, "reviews": 0}

        sku_name, base_rating, review_count = sku_row
        catalog_meta = {
            "name": sku_name,
            "rating": base_rating,
            "reviews": review_count
        }

        # If query_text is not provided, query vector DB using the SKU name
        search_query = query_text if query_text else f"reviews for {sku_name}"

        # Retrieve up to 5 reviews matching the SKU
        results = self.vector_store.query(search_query, n_results=5, sku_filter=sku_id)
        
        filtered_reviews = []
        for doc, dist, meta in zip(results["documents"], results["distances"], results["metadatas"]):
            similarity = 1.0 - dist
            print(f"Evaluating review for {sku_id}: Similarity = {similarity:.4f} | Text: '{doc[:60]}...'")
            if similarity >= similarity_threshold:
                filtered_reviews.append({
                    "review_text": doc,
                    "rating": meta.get("rating"),
                    "similarity": similarity
                })

        # Gate check: Needs at least 2 reviews meeting the threshold
        if len(filtered_reviews) < 2:
            print(f"Evidence Gate FAILED (retained {len(filtered_reviews)} reviews). Triggering fallback mode.")
            res = (True, [], catalog_meta)
            self.evidence_cache[cache_key] = res
            return res
        
        print(f"Evidence Gate PASSED (retained {len(filtered_reviews)} reviews). Using RAG mode.")
        res = (False, filtered_reviews, catalog_meta)
        self.evidence_cache[cache_key] = res
        return res

    def get_cart_recommendations(self, cart_sku_ids):
        """
        Queries sku_catalog for complementary items matching the exact categories of items currently in the cart.
        """
        if not cart_sku_ids:
            return []

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Step 1: Get categories of items currently in cart
        placeholders = ",".join(["?"] * len(cart_sku_ids))
        cursor.execute(f"SELECT DISTINCT category FROM sku_catalog WHERE sku_id IN ({placeholders})", list(cart_sku_ids))
        cart_categories = [r[0] for r in cursor.fetchall() if r[0]]

        recommendations = []

        # Step 2: Fetch items from the SAME categories first
        if cart_categories:
            cat_placeholders = ",".join(["?"] * len(cart_categories))
            sku_placeholders = ",".join(["?"] * len(cart_sku_ids))
            
            same_cat_query = f"""
                SELECT sku_id, name, price, category, base_rating, review_count
                FROM sku_catalog
                WHERE category IN ({cat_placeholders})
                  AND sku_id NOT IN ({sku_placeholders})
                ORDER BY base_rating DESC, review_count DESC
            """
            cursor.execute(same_cat_query, list(cart_categories) + list(cart_sku_ids))
            same_cat_rows = cursor.fetchall()

            for row in same_cat_rows:
                sku_id, name, price, category, rating, review_count = row
                strength = max(1, review_count // 50)
                neighbor_text = f"⚡ {strength}+ neighbors in DLF Phase 3 bought this with your items"
                recommendations.append({
                    "sku_id": sku_id,
                    "name": name,
                    "price": price,
                    "category": category,
                    "rating": rating,
                    "review_count": review_count,
                    "strength": strength,
                    "neighbor_validation_text": neighbor_text
                })

        # Step 3: Fallback to general top-rated items if no same-category items found
        if len(recommendations) < 2:
            existing_recs_skus = [r["sku_id"] for r in recommendations] + list(cart_sku_ids)
            ex_placeholders = ",".join(["?"] * len(existing_recs_skus))

            fallback_query = f"""
                SELECT sku_id, name, price, category, base_rating, review_count
                FROM sku_catalog
                WHERE sku_id NOT IN ({ex_placeholders})
                ORDER BY base_rating DESC, review_count DESC
            """
            cursor.execute(fallback_query, existing_recs_skus)
            fallback_rows = cursor.fetchall()

            for row in fallback_rows:
                sku_id, name, price, category, rating, review_count = row
                strength = max(1, review_count // 50)
                neighbor_text = f"⚡ {strength}+ neighbors in DLF Phase 3 bought this with your items"
                recommendations.append({
                    "sku_id": sku_id,
                    "name": name,
                    "price": price,
                    "category": category,
                    "rating": rating,
                    "review_count": review_count,
                    "strength": strength,
                    "neighbor_validation_text": neighbor_text
                })

        conn.close()
        return recommendations

if __name__ == "__main__":
    # Local unit test
    router = IntegrationRouter(use_local_model=False)

    print("\n=== Test 1: Evidence Gate for SKU-SUNSCREEN (Expect PASS if similarity matches) ===")
    # Search for sunscreen using keywords present in our synthetic data
    fallback, reviews, meta = router.run_evidence_gate("SKU-SUNSCREEN", "sunscreen hot sun summer commute", similarity_threshold=0.01)
    print(f"Fallback Mode: {fallback}")
    print(f"Metadata: {meta}")
    print(f"Review count passed gate: {len(reviews)}")

    print("\n=== Test 2: Evidence Gate (Expect FAIL / Fallback due to high threshold or mismatch) ===")
    fallback, reviews, meta = router.run_evidence_gate("SKU-SUNSCREEN", "usb fast charging cable", similarity_threshold=0.90)
    print(f"Fallback Mode: {fallback}")

    print("\n=== Test 3: Cart Recommendations (Staples: Coffee and Face Wash) ===")
    recs = router.get_cart_recommendations(["SKU-STAPLE-COFFEE", "SKU-STAPLE-WASH"])
    for r in recs:
        print(f"Recommended SKU: {r['sku_id']} ({r['name']}) | Price: ₹{r['price']} | Strengh: {r['strength']} | Badge: '{r['neighbor_validation_text']}'")
