import os
import json
import sqlite3
from src.vector_store import VectorStore

DB_PATH = "data/blinkit_local.db"
CLEANED_REVIEWS_PATH = "data/cleaned_reviews.json"
ORDER_HISTORY_PATH = "data/order_history.json"

def setup_sqlite_database():
    print(f"Setting up SQLite database at {DB_PATH}...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create sku_catalog table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sku_catalog (
            sku_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            base_rating REAL,
            review_count INTEGER DEFAULT 0
        )
    """)

    # Create co_occurrences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS co_occurrences (
            staple_sku TEXT NOT NULL,
            rec_sku TEXT NOT NULL,
            co_occurrence_count INTEGER DEFAULT 0,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            PRIMARY KEY (staple_sku, rec_sku)
        )
    """)

    conn.commit()
    conn.close()
    print("SQLite tables created successfully.")

def populate_sku_catalog():
    print("Populating SKU catalog...")
    # Standard catalog items (staples and non-grocery MVP items)
    catalog_items = [
        # Staples (Grocery)
        ("SKU-STAPLE-COFFEE", "Premium Coffee Beans", 450.0, "Grocery", 4.8, 1250),
        ("SKU-STAPLE-MILK", "Organic Whole Milk 1L", 75.0, "Grocery", 4.7, 4500),
        ("SKU-STAPLE-BREAD", "Whole Wheat Bread 400g", 50.0, "Grocery", 4.5, 3800),
        ("SKU-APPLES", "Fresh Royal Gala Apples 500g", 120.0, "Grocery", 4.8, 1420),

        # Beauty / Skincare
        ("SKU-STAPLE-WASH", "Foaming Face Wash", 299.0, "Beauty/Skincare", 4.6, 920),
        ("SKU-SUNSCREEN", "Neutrogena Sunscreen SPF 50 Mini", 185.0, "Beauty/Skincare", 4.8, 120),
        ("SKU-LIPBALM", "Nivea Strawberry Shine Lip Balm 4.8g", 149.0, "Beauty/Skincare", 4.7, 540),
        ("SKU-SHAMPOO", "L'Oreal Paris Extraordinary Oil Shampoo 180ml", 249.0, "Beauty/Skincare", 4.7, 830),

        # Electronics
        ("SKU-CABLE", "USB Type-C Fast Charging Cable", 150.0, "Electronics", 4.5, 850),
        ("SKU-BLENDER", "NutriPro Portable Personal Blender 300W", 999.0, "Electronics", 4.6, 380),
        ("SKU-AIRPODS", "Apple AirPods Pro (2nd Gen)", 19999.0, "Electronics", 4.9, 2100),
        ("SKU-SPEAKER", "JBL Go 3 Eco Portable Bluetooth Speaker", 2499.0, "Electronics", 4.8, 1750),

        # Clothing
        ("SKU-SCRUNCHIE", "Silk Hair Scrunchies Pack of 3", 99.0, "Clothing", 4.7, 320),
        ("SKU-SOCKS", "Ankle Cotton Socks Pack of 2", 120.0, "Clothing", 4.4, 95),
        ("SKU-TSHIRT", "Classic Oversized Cotton T-Shirt", 499.0, "Clothing", 4.5, 430),
        ("SKU-JEANS", "Slim Fit Dark Blue Denim Jeans", 1299.0, "Clothing", 4.6, 610)
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for item in catalog_items:
        cursor.execute("""
            INSERT OR REPLACE INTO sku_catalog (sku_id, name, price, category, base_rating, review_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, item)

    conn.commit()
    conn.close()
    print(f"Populated {len(catalog_items)} items in sku_catalog.")

def populate_co_occurrences():
    print("Parsing order history and populating co-occurrences...")
    if not os.path.exists(ORDER_HISTORY_PATH):
        print(f"Order history file not found at {ORDER_HISTORY_PATH}. Skipping co-occurrence mapping.")
        return

    with open(ORDER_HISTORY_PATH, 'r', encoding='utf-8') as f:
        transactions = json.load(f)

    # Dictionary to count co-occurrences: {(staple_sku, rec_sku): count}
    co_counts = {}
    # Dictionary to keep track of metadata of recommendation items
    rec_meta = {}

    for txn in transactions:
        items = txn.get("items", [])
        
        # Split items into staples (grocery) and non-grocery add-ons (recommendation candidates)
        staples = [item for item in items if item.get("category") == "Grocery"]
        add_ons = [item for item in items if item.get("category") in ["Electronics", "Beauty/Skincare", "Clothing"]]

        for staple in staples:
            for addon in add_ons:
                staple_sku = staple["sku_id"]
                addon_sku = addon["sku_id"]
                key = (staple_sku, addon_sku)
                
                # Count the pair
                co_counts[key] = co_counts.get(key, 0) + 1
                
                # Cache the recommendation item metadata
                rec_meta[addon_sku] = {
                    "price": addon["price"],
                    "category": addon["category"]
                }

    # Insert into SQLite co_occurrences table
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for (staple_sku, addon_sku), count in co_counts.items():
        meta = rec_meta[addon_sku]
        cursor.execute("""
            INSERT OR REPLACE INTO co_occurrences (staple_sku, rec_sku, co_occurrence_count, price, category)
            VALUES (?, ?, ?, ?, ?)
        """, (staple_sku, addon_sku, count, meta["price"], meta["category"]))

    conn.commit()
    conn.close()
    print(f"Populated {len(co_counts)} co-occurrence pairs in SQLite.")

def index_cleaned_reviews_in_vector_db():
    print("Ingesting and indexing cleaned reviews into vector store...")
    if not os.path.exists(CLEANED_REVIEWS_PATH):
        print(f"Cleaned reviews file not found at {CLEANED_REVIEWS_PATH}. Ingestion skipped.")
        return

    with open(CLEANED_REVIEWS_PATH, 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    # Initialize VectorStore (use fallback mode model = False to guarantee quick execution)
    vector_store = VectorStore(persist_directory="data/chroma_db", use_local_model=False)

    documents = []
    metadatas = []
    ids = []

    for review in reviews:
        documents.append(review["review_text"])
        metadatas.append({
            "sku_id": review["sku_id"],
            "category": review["category"],
            "rating": review["rating"],
            "location": review["location"]
        })
        ids.append(review["review_id"])

    if documents:
        vector_store.add_documents(documents, metadatas, ids)
        print(f"Successfully indexed {len(documents)} reviews.")
    else:
        print("No documents found to index.")

def main():
    setup_sqlite_database()
    populate_sku_catalog()
    populate_co_occurrences()
    index_cleaned_reviews_in_vector_db()
    print("Phase 2 setup completed successfully!")

if __name__ == "__main__":
    main()
