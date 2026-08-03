import sqlite3
from src.vector_store import VectorStore

DB_PATH = "data/blinkit_local.db"

def verify_sqlite():
    print("\n--- Verifying SQLite Data ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query catalog
    cursor.execute("SELECT sku_id, name, price, category, base_rating, review_count FROM sku_catalog")
    catalog = cursor.fetchall()
    print(f"Catalog items count: {len(catalog)}")
    for item in catalog[:3]:
        print(f"  SKU: {item[0]} | Name: {item[1]} | Price: {item[2]} | Cat: {item[3]} | Rating: {item[4]} (Reviews: {item[5]})")

    # Query co-occurrences
    cursor.execute("SELECT staple_sku, rec_sku, co_occurrence_count FROM co_occurrences")
    co_occurs = cursor.fetchall()
    print(f"\nCo-occurrence pairs count: {len(co_occurs)}")
    for pair in co_occurs[:4]:
         print(f"  Staple: {pair[0]} <-> Rec: {pair[1]} | Count: {pair[2]}")

    conn.close()

def verify_vector_store():
    print("\n--- Verifying Vector Store Retrieval ---")
    vector_store = VectorStore(persist_directory="data/chroma_db", use_local_model=False)

    # Let's search for "sunscreen" for target SKU "SKU-SUNSCREEN"
    query = "non sticky sunscreen for summer"
    print(f"Query: '{query}' for SKU-SUNSCREEN...")
    
    results = vector_store.query(query, n_results=3, sku_filter="SKU-SUNSCREEN")
    
    print(f"Found {len(results['documents'])} matches:")
    for doc, dist, meta in zip(results["documents"], results["distances"], results["metadatas"]):
        similarity = 1.0 - dist
        print(f"  Similarity: {similarity:.4f} | Rating: {meta['rating']} | Review: '{doc}'")

if __name__ == "__main__":
    verify_sqlite()
    verify_vector_store()
