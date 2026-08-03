import streamlit as st
import sqlite3
import os
import json
import time
import textwrap
from src.integration import IntegrationRouter
from src.trust_engine import TrustEngine

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Automated First-Boot Database Initialization for Streamlit Cloud
if not os.path.exists("data/blinkit_local.db"):
    import subprocess
    print("Database missing. Initializing SQLite catalog and ChromaDB vector index...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    subprocess.run(["python3", "src/db_setup.py"], check=True, env=env)

# Page Config - Set layout to wide for full desktop experience
st.set_page_config(
    page_title="Blinkit Contextual Trust & Recs Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Style Block with Tailwind and Google Fonts
st.markdown(textwrap.dedent("""
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Outfit:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">

<script>
    tailwind.config = {
        theme: {
            extend: {
                fontFamily: {
                    sans: ['Inter', 'sans-serif'],
                },
                colors: {
                    blinkit: {
                        yellow: '#F7C200',
                        yellowLight: '#FFF9E5',
                        yellowBanner: '#FFD203',
                        green: '#0C831F',
                        greenHover: '#096317',
                        dark: '#1C1C1C',
                        bg: '#FCFCFA',
                        cardBorder: '#EBEBEB'
                    }
                }
            }
        }
    }
</script>

<style>
/* Global Background and Typography */
.stApp {
    background-color: #FCFCFA !important;
    color: #1C1C1C !important;
    font-family: 'Inter', sans-serif;
}

.logo-tile {
    background-color: #F7C200;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 6px 14px;
    font-weight: 900;
    letter-spacing: -0.5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
}

/* Sleek Visually Appealing Search Bar Styling */
div[data-testid="stTextInput"] input {
    background-color: #F1F5F9 !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 12px 18px 12px 44px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #1E293B !important;
    transition: all 0.2s ease !important;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="%2394A3B8" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 14px center !important;
    background-size: 20px 20px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
}

div[data-testid="stTextInput"] input:focus {
    background-color: #FFFFFF !important;
    border-color: #0C831F !important;
    box-shadow: 0 0 0 3px rgba(12, 131, 31, 0.15) !important;
    outline: none !important;
}

.font-outfit {
    font-family: 'Outfit', sans-serif;
}

.glass-header {
    backdrop-filter: blur(12px);
    background: rgba(255, 255, 255, 0.95);
    border-bottom: 1px solid #EBEBEB;
}

.sticky-checkout {
    position: sticky;
    top: 20px;
}

/* Hide Streamlit Sidebar and collapse arrow completely */
[data-testid="stSidebar"], 
[data-testid="stSidebarNav"], 
[data-testid="stSidebarCollapsedControl"],
button[aria-label="Expand sidebar"],
button[aria-label="Collapse sidebar"] {
    display: none !important;
}

/* Premium Styled Streamlit buttons inside product cards */
div.stButton > button {
    background-color: #0C831F !important;
    color: white !important;
    border-radius: 12px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
    border: none !important;
    padding: 8px 24px !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}

div.stButton > button:hover {
    background-color: #0a6c1a !important;
    transform: scale(1.03) !important;
    box-shadow: 0 4px 12px rgba(12, 131, 31, 0.25) !important;
}

/* Detail View Button overrides */
div.stButton > button.secondary-btn {
    background-color: transparent !important;
    color: #0C831F !important;
    border: 2px solid #0C831F !important;
}

div.stButton > button.secondary-btn:hover {
    background-color: rgba(12, 131, 31, 0.05) !important;
    color: #0a6c1a !important;
}

/* Uniform product card grid */
.product-card {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 290px;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    transition: box-shadow 0.2s ease;
}

.product-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.product-card-image-wrap {
    height: 140px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    border-radius: 0.75rem;
    background: #ffffff;
    padding: 8px;
    border: 1px solid #f3f4f6;
    margin-bottom: 0.5rem;
    flex-shrink: 0;
}

.product-card-image {
    width: 110px;
    height: 110px;
    max-width: 110px;
    max-height: 110px;
    object-fit: contain;
    display: block;
    margin: auto;
}

.product-card-body {
    display: flex;
    flex-direction: column;
    flex: 1;
}

.product-card-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    color: #1f2937;
    font-size: 0.875rem !important;
    line-height: 1.2;
    min-height: 2.2rem;
    margin: 0;
}

.product-card-meta {
    font-size: 0.7rem;
    color: #6b7280;
    margin-top: 0.15rem;
    font-weight: 500;
}

.product-card-price-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid #f3f4f6;
}

.product-card-price {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    color: #111827;
    font-size: 0.95rem;
}

.product-card-add-btn {
    background-color: #0C831F !important;
    color: white !important;
    border: 1px solid #0C831F !important;
    border-radius: 6px !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    font-family: 'Outfit', sans-serif !important;
    padding: 4px 14px !important;
    text-decoration: none !important;
    text-align: center !important;
    display: inline-block !important;
    transition: all 0.2s ease !important;
    text-transform: uppercase !important;
}

.product-card-add-btn:hover {
    background-color: #0a6c1a !important;
    transform: scale(1.05) !important;
}

div[data-testid="column"]:has(.product-card) {
    display: flex;
    flex-direction: column;
}

div[data-testid="column"]:has(.product-card) .product-card {
    flex: 1;
}

.customer-review-card {
    background: white;
    border: 1px solid #f3f4f6;
    border-radius: 0.75rem;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.customer-review-card .review-stars {
    letter-spacing: 0.05em;
}

.rating-bar-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
}

.rating-bar-track {
    flex: 1;
    height: 0.5rem;
    background: #f3f4f6;
    border-radius: 9999px;
    overflow: hidden;
}

.rating-bar-fill {
    height: 100%;
    background: #f59e0b;
    border-radius: 9999px;
}
</style>
"""), unsafe_allow_html=True)

# Initialize Session States
if "cart" not in st.session_state:
    st.session_state.cart = {} # {sku_id: {"name": name, "price": price, "qty": qty, "category": cat}}
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "active_category" not in st.session_state:
    st.session_state.active_category = "All"
if "show_cart" not in st.session_state:
    st.session_state.show_cart = False
if "evidence_threshold" not in st.session_state:
    st.session_state.evidence_threshold = 0.90
if "latency_metrics" not in st.session_state:
    st.session_state.latency_metrics = {"vector_db": 0.0, "sqlite": 0.0, "llm": 0.0}

# DB Setup & Router Inits
DB_PATH = "data/blinkit_local.db"
router = IntegrationRouter(use_local_model=False)
trust_engine = TrustEngine()

# Helpers
def get_cart_subtotal():
    return sum(item["price"] * item["qty"] for item in st.session_state.cart.values())

def get_cart_count():
    return sum(item["qty"] for item in st.session_state.cart.values())

def add_to_cart(sku_id, name, price, category):
    if "cart" not in st.session_state:
        st.session_state.cart = {}
    if sku_id in st.session_state.cart:
        st.session_state.cart[sku_id]["qty"] += 1
    else:
        st.session_state.cart[sku_id] = {
            "name": name,
            "price": price,
            "qty": 1,
            "category": category
        }
    st.session_state.show_cart = True
    st.toast(f"Added {name} to cart!", icon="🛒")

def get_product_image_url(sku_id, name=""):
    mapping = {
        "SKU-STAPLE-COFFEE": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&auto=format&fit=crop",
        "SKU-STAPLE-WASH": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop",
        "SKU-STAPLE-MILK": "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=500&auto=format&fit=crop",
        "SKU-STAPLE-BREAD": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop",
        "SKU-SUNSCREEN": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&auto=format&fit=crop",
        "SKU-LIPBALM": "https://images.unsplash.com/photo-1617897903246-719242758050?w=500&auto=format&fit=crop",
        "SKU-CABLE": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&auto=format&fit=crop",
        "SKU-BLENDER": "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=500&auto=format&fit=crop",
        "SKU-AIRPODS": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=500&auto=format&fit=crop",
        "SKU-SCRUNCHIE": "https://images.unsplash.com/photo-1620331311520-246422fd82f9?w=500&auto=format&fit=crop",
        "SKU-SOCKS": "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=500&auto=format&fit=crop",
        "SKU-TSHIRT": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop",
        "SKU-JEANS": "https://images.unsplash.com/photo-1542272604-780c36856842?w=500&auto=format&fit=crop"
    }
    
    if sku_id in mapping:
        return mapping[sku_id]
        
    # Keyword fallback matching
    name_lower = name.lower()
    if "coffee" in name_lower:
        return "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&auto=format&fit=crop"
    elif "bread" in name_lower or "toast" in name_lower or "pav" in name_lower:
        return "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop"
    elif "balm" in name_lower or "lip" in name_lower:
        return "https://images.unsplash.com/photo-1617897903246-719242758050?w=500&auto=format&fit=crop"
    elif "wash" in name_lower or "cream" in name_lower or "lotion" in name_lower or "cleanser" in name_lower:
        return "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop"
    elif "milk" in name_lower or "dairy" in name_lower or "dahi" in name_lower:
        return "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=500&auto=format&fit=crop"
    elif "sunscreen" in name_lower or "spf" in name_lower:
        return "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&auto=format&fit=crop"
    elif "blender" in name_lower or "juicer" in name_lower or "mixer" in name_lower:
        return "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=500&auto=format&fit=crop"
    elif "airpod" in name_lower or "earbud" in name_lower or "headphone" in name_lower:
        return "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=500&auto=format&fit=crop"
    elif "cable" in name_lower or "charge" in name_lower or "usb" in name_lower:
        return "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&auto=format&fit=crop"
    elif "shirt" in name_lower or "t-shirt" in name_lower or "top" in name_lower:
        return "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop"
    elif "jean" in name_lower or "denim" in name_lower or "pant" in name_lower or "trouser" in name_lower:
        return "https://images.unsplash.com/photo-1542272604-780c36856842?w=500&auto=format&fit=crop"
    elif "scrunchie" in name_lower or "hair" in name_lower:
        return "https://images.unsplash.com/photo-1620331311520-246422fd82f9?w=500&auto=format&fit=crop"
    elif "sock" in name_lower or "apparel" in name_lower:
        return "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=500&auto=format&fit=crop"
        
    return "https://images.unsplash.com/photo-1542838132-92c53300491e?w=500&auto=format&fit=crop"

# Process optional deep-link query params on first load without forcing extra re-reruns
if st.query_params and "action" in st.query_params:
    action = st.query_params["action"]
    sku = st.query_params.get("sku")
    
    if action == "toggle_cart":
        st.session_state.show_cart = not st.session_state.show_cart
    elif action == "open_cart":
        st.session_state.show_cart = True
    elif action == "close_cart":
        st.session_state.show_cart = False
    elif action == "checkout":
        st.session_state.cart = {}
        st.session_state.show_cart = False
        st.toast("Order placed successfully! Arriving in 16 minutes. 🚀", icon="🎉")
    elif action == "detail":
        if sku:
            st.session_state.selected_product = sku
            st.session_state.show_cart = False
    elif action in ["add", "inc"]:
        if sku:
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, price, category FROM sku_catalog WHERE sku_id = ?", (sku,))
            row = cursor.fetchone()
            conn.close()
            if row:
                name, price, category = row
                add_to_cart(sku, name, price, category)
    elif action == "dec":
        if sku and sku in st.session_state.cart:
            st.session_state.cart[sku]["qty"] -= 1
            if st.session_state.cart[sku]["qty"] <= 0:
                del st.session_state.cart[sku]
            st.toast("Updated cart!", icon="🛒")
    st.query_params.clear()

def render_product_card_html(sku_id, image_url, name, price, category, meta_text):
    return textwrap.dedent(f"""
    <div class="product-card">
        <a href="?action=detail&sku={sku_id}" target="_self" style="text-decoration: none; color: inherit; display: block; cursor: pointer;">
            <div class="product-card-image-wrap">
                <img class="product-card-image" src="{image_url}" alt="{name}">
            </div>
            <div class="product-card-body">
                <h4 class="product-card-title">{name}</h4>
                <p class="product-card-meta">{meta_text}</p>
            </div>
            <div class="product-card-price-row">
                <span class="product-card-price">₹{price:.0f}</span>
            </div>
        </a>
    </div>
    """)


def stars_html(rating):
    filled = max(0, min(5, round(rating)))
    filled_stars = f'<span style="color: #FFB800; font-size: 16px; font-weight: bold; letter-spacing: 2px;">{"★" * filled}</span>'
    empty_stars = f'<span style="color: #CBD5E1; font-size: 16px; font-weight: bold; letter-spacing: 2px;">{"☆" * (5 - filled)}</span>'
    return f'{filled_stars}{empty_stars}'


def get_sample_customer_reviews(product_name, category):
    name_l = product_name.lower()

    if "coffee" in name_l:
        pool = [
            {"author": "Priya S.", "rating": 5, "date": "2 weeks ago", "text": "Rich aroma and freshly roasted taste. Makes a perfect morning cup every time."},
            {"author": "Rahul M.", "rating": 4, "date": "1 month ago", "text": "Good quality beans and smooth flavour. Packaging could be a bit sturdier though."},
            {"author": "Ananya K.", "rating": 2, "date": "3 weeks ago", "text": "Taste felt a little stale compared to what I expected at this price point."},
            {"author": "Vikram D.", "rating": 5, "date": "5 days ago", "text": "Delivered in 10 mins and the beans were fresh. Will definitely reorder."},
            {"author": "Sneha P.", "rating": 3, "date": "2 months ago", "text": "Decent coffee but nothing extraordinary. Works fine for daily use."},
        ]
    elif "wash" in name_l or "face" in name_l:
        pool = [
            {"author": "Neha R.", "rating": 5, "date": "1 week ago", "text": "Gentle on skin and removes oil without drying. Love the light fragrance."},
            {"author": "Arjun T.", "rating": 4, "date": "3 weeks ago", "text": "Foams nicely and skin feels clean. Slightly pricey for the quantity."},
            {"author": "Kavita L.", "rating": 1, "date": "2 weeks ago", "text": "Broke me out badly. Had to stop using after three days."},
            {"author": "Mohit G.", "rating": 5, "date": "4 days ago", "text": "Best face wash I've ordered on Blinkit. Non-sticky and refreshing."},
            {"author": "Divya N.", "rating": 3, "date": "1 month ago", "text": "Average product. Cleans well but didn't notice any major improvement."},
        ]
    elif "milk" in name_l or "dairy" in name_l:
        pool = [
            {"author": "Ramesh K.", "rating": 5, "date": "3 days ago", "text": "Always fresh and well-chilled on delivery. Taste is consistently good."},
            {"author": "Pooja A.", "rating": 4, "date": "1 week ago", "text": "Good quality organic milk. Cap was slightly loose once but product was fine."},
            {"author": "Suresh V.", "rating": 2, "date": "2 weeks ago", "text": "Received a packet close to expiry date. Disappointed with that batch."},
            {"author": "Meera J.", "rating": 5, "date": "6 days ago", "text": "Creamy and fresh — perfect for my morning chai and cereals."},
            {"author": "Amit B.", "rating": 3, "date": "3 weeks ago", "text": "Okay taste, nothing special. Delivery was quick as always."},
        ]
    elif "sunscreen" in name_l or "spf" in name_l:
        pool = [
            {"author": "Isha M.", "rating": 5, "date": "5 days ago", "text": "Absorbs quickly with no white cast. Great for daily Gurgaon commute."},
            {"author": "Rohan S.", "rating": 4, "date": "2 weeks ago", "text": "Non-sticky formula and good SPF protection. Tube is smaller than expected."},
            {"author": "Tanvi P.", "rating": 2, "date": "1 month ago", "text": "Caused mild irritation on sensitive skin. Had to switch to another brand."},
            {"author": "Aditi C.", "rating": 5, "date": "1 week ago", "text": "Lightweight and doesn't feel greasy at all. Highly recommend for summers."},
            {"author": "Karan H.", "rating": 3, "date": "3 weeks ago", "text": "Does the job but needs reapplication often. Average value for money."},
        ]
    elif "cable" in name_l or "charge" in name_l or "usb" in name_l:
        pool = [
            {"author": "Dev P.", "rating": 5, "date": "4 days ago", "text": "Fast charging works perfectly with my phone. Build feels solid."},
            {"author": "Nisha W.", "rating": 4, "date": "2 weeks ago", "text": "Good cable for the price. Charges quickly but connector is a tad tight."},
            {"author": "Harsh L.", "rating": 1, "date": "3 weeks ago", "text": "Stopped working within a week. Connection became loose very quickly."},
            {"author": "Varun E.", "rating": 5, "date": "1 week ago", "text": "Durable and tangle-free. Exactly what I needed for work travel."},
            {"author": "Shreya F.", "rating": 3, "date": "1 month ago", "text": "Works fine for now but feels cheaper than branded alternatives."},
        ]
    elif "sock" in name_l or "apparel" in name_l or "scrunchie" in name_l or "hair" in name_l:
        pool = [
            {"author": "Aisha Q.", "rating": 5, "date": "6 days ago", "text": "Soft fabric and comfortable fit. Colors look exactly like the photos."},
            {"author": "Manish D.", "rating": 4, "date": "2 weeks ago", "text": "Good quality for daily wear. Sizing runs slightly small."},
            {"author": "Ritu O.", "rating": 2, "date": "3 weeks ago", "text": "Material felt thin after first wash. Expected better durability."},
            {"author": "Farhan Z.", "rating": 5, "date": "1 week ago", "text": "Great value pick. Comfortable and delivered super fast."},
            {"author": "Lakshmi I.", "rating": 3, "date": "1 month ago", "text": "Average quality — fine for the price but not premium."},
        ]
    else:
        pool = [
            {"author": "Priya S.", "rating": 5, "date": "1 week ago", "text": f"Really happy with {product_name}. Quality exceeded my expectations."},
            {"author": "Rahul M.", "rating": 4, "date": "2 weeks ago", "text": "Good product overall. Does what it promises and arrived quickly."},
            {"author": "Ananya K.", "rating": 2, "date": "3 weeks ago", "text": "Not worth the hype. Quality felt below average for the price."},
            {"author": "Vikram D.", "rating": 5, "date": "5 days ago", "text": "Excellent purchase — would recommend to anyone in DLF Phase 3."},
            {"author": "Sneha P.", "rating": 3, "date": "1 month ago", "text": "It's okay. Neither great nor terrible — just an average buy."},
        ]

    return pool


def render_rating_breakdown_html(base_rating, review_count):
    distribution = {
        5: max(5, int(review_count * 0.45)),
        4: max(3, int(review_count * 0.25)),
        3: max(2, int(review_count * 0.15)),
        2: max(1, int(review_count * 0.08)),
        1: max(1, int(review_count * 0.07)),
    }
    total = sum(distribution.values())
    rows = []
    for star in range(5, 0, -1):
        pct = int((distribution[star] / total) * 100)
        rows.append(
            f'<div class="rating-bar-row">'
            f'<span class="w-8">{star} ★</span>'
            f'<div class="rating-bar-track"><div class="rating-bar-fill" style="width: {pct}%"></div></div>'
            f'<span class="w-8 text-right">{pct}%</span>'
            f'</div>'
        )
    return "".join(rows)


def render_customer_reviews_html(reviews):
    cards = []
    for review in reviews:
        stars = stars_html(review["rating"])
        badge_bg = "#ecfdf5" if review["rating"] >= 4 else "#fffbeb"
        badge_color = "#0C831F" if review["rating"] >= 4 else "#d97706"
        cards.append(
            f'<div style="background: #ffffff; border: 1px solid #f1f5f9; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); transition: all 0.2s ease;">'
            f'<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span style="font-family: \'Outfit\', sans-serif; font-size: 14px; font-weight: 800; color: #0f172a;">{review["author"]}</span>'
            f'<span style="font-size: 10px; font-weight: 700; color: {badge_color}; background: {badge_bg}; padding: 2px 8px; border-radius: 12px;">✓ Verified Buyer</span>'
            f'</div>'
            f'<span style="font-size: 11px; font-weight: 500; color: #94a3b8;">{review["date"]}</span>'
            f'</div>'
            f'<div style="margin-bottom: 6px;">{stars}</div>'
            f'<p style="font-size: 13px; color: #475569; line-height: 1.5; margin: 0; font-weight: 400;">{review["text"]}</p>'
            f'</div>'
        )
    return "".join(cards)


def render_cart_drawer():
    if not st.session_state.show_cart:
        return

    # Header Row
    h_col1, h_col2 = st.columns([7, 3])
    with h_col1:
        st.markdown('<h3 style="font-family: \'Outfit\', sans-serif; font-size: 21px; font-weight: 900; color: #0f172a; margin: 0;">🛒 My Cart</h3>', unsafe_allow_html=True)
    with h_col2:
        if st.button("✕ Close", key="cart_drawer_close_btn", use_container_width=True):
            st.session_state.show_cart = False
            st.rerun()

    # If cart is empty
    if not st.session_state.cart:
        st.markdown(textwrap.dedent("""
        <div style="background: white; border-radius: 16px; padding: 32px 18px; text-align: center; border: 1px solid #e2e8f0; font-family: 'Outfit', sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
            <div style="font-size: 48px; margin-bottom: 10px;">🛒</div>
            <h4 style="font-size: 18px; font-weight: 900; color: #0f172a; margin: 0 0 8px 0;">Your cart is empty</h4>
            <p style="font-size: 14px; color: #64748b; margin: 0; line-height: 1.4;">Explore fresh products and add items to unlock 10-minute delivery in DLF Phase 3!</p>
        </div>
        """), unsafe_allow_html=True)
        return

    total_items = get_cart_count()
    subtotal = get_cart_subtotal()
    delivery_charge = 25.0
    handling_charge = 2.0
    surge_charge = 30.0
    grand_total = subtotal + delivery_charge + handling_charge + surge_charge

    # Delivery Badge
    st.markdown(textwrap.dedent(f"""
    <div style="background: white; border-radius: 14px; padding: 14px 16px; border: 1px solid #e2e8f0; margin-top: 10px; margin-bottom: 12px; font-family: 'Outfit', sans-serif; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 24px;">⏱️</span>
            <div>
                <h4 style="font-size: 15px; font-weight: 900; color: #0f172a; margin: 0;">Delivery in 16 minutes</h4>
                <p style="font-size: 13px; color: #64748b; margin: 2px 0 0 0; font-weight: 600;">Shipment of {total_items} item{"s" if total_items != 1 else ""}</p>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)

    # Cart Items List
    for sku_id, item in list(st.session_state.cart.items()):
        img = get_product_image_url(sku_id, item["name"])
        st.markdown(textwrap.dedent(f"""
        <div style="background: white; border-radius: 12px; padding: 12px 14px; border: 1px solid #e2e8f0; margin-bottom: 8px; font-family: 'Outfit', sans-serif;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <img src="{img}" style="width: 50px; height: 50px; object-fit: contain; border-radius: 8px; border: 1px solid #e2e8f0; padding: 3px; background: white; flex-shrink: 0;">
                <div style="flex: 1;">
                    <p style="font-size: 14px; font-weight: 800; color: #0f172a; margin: 0; line-height: 1.3;">{item["name"]}</p>
                    <p style="font-size: 14px; font-weight: 900; color: #0C831F; margin: 3px 0 0 0;">₹{item["price"] * item["qty"]:.0f}</p>
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)
        
        q_col1, q_col2, q_col3 = st.columns([1, 1, 1])
        with q_col1:
            if st.button("−", key=f"drawer_dec_{sku_id}", use_container_width=True):
                st.session_state.cart[sku_id]["qty"] -= 1
                if st.session_state.cart[sku_id]["qty"] <= 0:
                    del st.session_state.cart[sku_id]
                st.rerun()
        with q_col2:
            st.markdown(f'<div style="text-align: center; font-weight: 900; font-size: 15px; font-family: \'Outfit\', sans-serif; margin-top: 4px; color: #0f172a;">Qty: {item["qty"]}</div>', unsafe_allow_html=True)
        with q_col3:
            if st.button("+", key=f"drawer_inc_{sku_id}", use_container_width=True):
                st.session_state.cart[sku_id]["qty"] += 1
                st.rerun()

    # Category-Matched Recommendations
    cart_skus = list(st.session_state.cart.keys())
    cart_items_list = list(st.session_state.cart.values())
    first_item_name = cart_items_list[0]["name"] if cart_items_list else "this item"
    recommendations = router.get_cart_recommendations(cart_skus)
    valid_recs = [r for r in recommendations if r["sku_id"] not in st.session_state.cart]

    if valid_recs:
        st.markdown(textwrap.dedent("""
        <div style="margin-top: 16px; margin-bottom: 10px; font-family: 'Outfit', sans-serif;">
            <h4 style="font-size: 13px; font-weight: 900; color: #0f172a; text-transform: uppercase; margin: 0; letter-spacing: 0.3px;">People who bought this also bought this</h4>
        </div>
        """), unsafe_allow_html=True)

        indian_names = ["Saksham", "Aarav", "Priya", "Rohan", "Ananya", "Dev", "Isha", "Karan", "Tanvi", "Aditya"]
        distances = ["0.5km", "0.8km", "1km", "1.2km", "1.5km"]

        for idx, r in enumerate(valid_recs[:2]):
            r_img = get_product_image_url(r["sku_id"], r["name"])
            person_name = indian_names[idx % len(indian_names)]
            dist = distances[idx % len(distances)]
            social_proof_text = f"⚡ {person_name} from {dist} distance also ordered {r['name']} when ordering {first_item_name}"

            r_col1, r_col2 = st.columns([7, 3])
            with r_col1:
                st.markdown(textwrap.dedent(f"""
                <div style="background: white; border-radius: 12px; padding: 10px 12px; border: 1px solid #e2e8f0; font-family: 'Outfit', sans-serif; margin-bottom: 4px;">
                    <span style="font-size: 11px; font-weight: 800; color: #0C831F; background: #ecfdf5; padding: 3px 8px; border-radius: 6px; display: inline-block; line-height: 1.3;">{social_proof_text}</span>
                    <p style="font-size: 14px; font-weight: 800; color: #0f172a; margin: 5px 0 0 0; line-height: 1.3;">{r["name"]}</p>
                    <p style="font-size: 13px; font-weight: 900; color: #475569; margin: 2px 0 0 0;">₹{r["price"]:.0f}</p>
                </div>
                """), unsafe_allow_html=True)
            with r_col2:
                if st.button("+ ADD", key=f"drawer_rec_add_{r['sku_id']}_{idx}", use_container_width=True):
                    add_to_cart(r["sku_id"], r["name"], r["price"], r["category"])
                    st.rerun()

    # Bill details & Checkout Button
    st.markdown(textwrap.dedent(f"""
    <div style="background: white; border-radius: 16px; padding: 16px; border: 1px solid #e2e8f0; margin-top: 16px; font-family: 'Outfit', sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
        <h4 style="font-size: 16px; font-weight: 900; color: #0f172a; margin: 0 0 12px 0;">Bill details</h4>
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #475569; margin-bottom: 6px; font-weight: 600;"><span>Items total</span><span style="font-weight: 800; color: #0f172a;">₹{subtotal:.0f}</span></div>
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #475569; margin-bottom: 6px; font-weight: 600;"><span>Delivery charge</span><span style="font-weight: 800; color: #0f172a;">₹{delivery_charge:.0f}</span></div>
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #475569; margin-bottom: 6px; font-weight: 600;"><span>Handling charge</span><span style="font-weight: 800; color: #0f172a;">₹{handling_charge:.0f}</span></div>
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #475569; margin-bottom: 6px; font-weight: 600;"><span>Surge charge</span><span style="font-weight: 800; color: #0f172a;">₹{surge_charge:.0f}</span></div>
        <div style="padding-top: 10px; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; margin-top: 8px; font-weight: 900; font-size: 17px; color: #0f172a;"><span>Grand Total</span><span style="color: #0C831F;">₹{grand_total:.0f}</span></div>
    </div>
    """), unsafe_allow_html=True)

    if st.button(f"Proceed to Pay • ₹{grand_total:.0f} ›", key="drawer_checkout_btn", use_container_width=True, type="primary"):
        st.session_state.cart = {}
        st.session_state.show_cart = False
        st.toast("Order placed successfully! Arriving in 16 minutes. 🚀", icon="🎉")
        st.rerun()




# --- DESKTOP NAVBAR HEADER ---
header_c1, header_c2 = st.columns([8, 3])
with header_c1:
    st.markdown(textwrap.dedent("""
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
        <div style="display: flex; align-items: center; cursor: pointer; user-select: none;">
            <span style="font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 900; color: #F7C200; background: #1C1C1C; padding: 2px 10px; border-radius: 8px 0 0 8px;">blink</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 900; color: #ffffff; background: #0C831F; padding: 2px 10px; border-radius: 0 8px 8px 0;">it</span>
        </div>
        <div style="display: flex; flex-direction: column; font-size: 12px; font-family: 'Outfit', sans-serif;">
            <span style="font-weight: 800; color: #111827;">Delivery in 8 minutes</span>
            <span style="color: #6b7280; font-weight: 600;">DLF Phase 3, Gurugram ▾</span>
        </div>
    </div>
    """), unsafe_allow_html=True)
with header_c2:
    subtotal = get_cart_subtotal()
    cart_count = get_cart_count()
    if st.button(f"🛒 My Cart ({cart_count}) • ₹{subtotal:.0f}", key="main_header_cart_button", use_container_width=True):
        st.session_state.show_cart = not st.session_state.show_cart
        st.rerun()

is_pdp_active = st.session_state.selected_product is not None

# 2. Main Page Search Box (Visually Appealing Search Bar)
search_col1, search_col2 = st.columns([10, 2])
with search_col1:
    search_q = st.text_input(
        "", 
        placeholder='Search "sunscreen", "basmati rice", "coffee" or "dahi"', 
        label_visibility="collapsed"
    )
with search_col2:
    if search_q:
        if st.button("Clear ✕"):
            search_q = ""
            st.session_state.active_category = "All"
            st.rerun()

# 3. Category Horizontal Row (Shown ONLY on Home/Catalog page, hidden on PDP)
if not is_pdp_active:
    st.markdown(textwrap.dedent("""
    <div class="my-6 border-b border-gray-200/50 pb-2">
    <p class="text-xs uppercase text-gray-400 font-bold tracking-wider font-outfit">Filter Categories</p>
    </div>
    """), unsafe_allow_html=True)

    col_all, col_gro, col_ele, col_beau, col_clo = st.columns(5)
    with col_all:
        if st.button("🛒 All Products", key="cat_all"): st.session_state.active_category = "All"
    with col_gro:
        if st.button("🍏 Grocery", key="cat_gro"): st.session_state.active_category = "Grocery"
    with col_ele:
        if st.button("⚡ Electronics", key="cat_ele"): st.session_state.active_category = "Electronics"
    with col_beau:
        if st.button("🧴 Beauty & Skincare", key="cat_beau"): st.session_state.active_category = "Beauty/Skincare"
    with col_clo:
        if st.button("👕 Clothing", key="cat_clo"): st.session_state.active_category = "Clothing"

# Determine state switches
is_searching = bool(search_q)
is_filtering = st.session_state.active_category != "All"

# Render side-by-side layout when cart drawer is open
if st.session_state.show_cart:
    main_view_col, cart_view_col = st.columns([7, 5])
    with cart_view_col:
        render_cart_drawer()
    page_container = main_view_col
else:
    page_container = st.container()

with page_container:
    if is_pdp_active:
        sku_id = st.session_state.selected_product
        
        # Ingest catalog details
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, category, base_rating, review_count FROM sku_catalog WHERE sku_id = ?", (sku_id,))
        sku_row = cursor.fetchone()
        conn.close()
        
        if sku_row:
            name, price, category, base_rating, review_count = sku_row
            image_url = get_product_image_url(sku_id, name)

            if st.button("← Back to Products", key="close_pdp"):
                st.session_state.selected_product = None
                st.rerun()

        # Two-Column Grid for PDP: pdp_col1 (Image & Buy CTA) | pdp_col2 (Specs & Customer Reviews)
        pdp_col1, pdp_col2 = st.columns([5, 7])

        with pdp_col1:
            # Main product image centered on a clean white card
            st.markdown(textwrap.dedent(f"""
            <div class="bg-white p-4 rounded-xl border border-gray-100 text-center mb-3 relative shadow-xs" style="height: 230px; display: flex; align-items: center; justify-content: center;">
                <span class="absolute top-2.5 left-2.5 bg-[#F7C200] text-gray-900 text-[10px] font-black px-2 py-0.5 rounded-md uppercase tracking-wider">
                    ⚡ 180+ bought in DLF Phase 3
                </span>
                <img style="width: 190px; height: 190px; max-width: 190px; max-height: 190px; object-fit: contain; display: block; margin: auto;" src="{image_url}" alt="{name}">
            </div>
            <div class="text-[11px] text-gray-400 font-medium mb-1">
                Home / <span class="text-gray-500 font-semibold">{category}</span> / <span class="text-gray-700 font-bold">{name}</span>
            </div>
            <h1 class="font-outfit text-xl font-black text-gray-900 leading-tight mb-1">{name}</h1>
            <div class="text-xs font-bold text-gray-500 mb-2">350 g • 8 mins delivery</div>
            """), unsafe_allow_html=True)

            # Price & Add to Cart button row
            price_col, btn_col = st.columns([5, 5])
            with price_col:
                st.markdown(textwrap.dedent(f"""
                <div>
                    <span class="font-outfit text-2xl font-black text-gray-900">₹{price:.0f}</span>
                    <span class="block text-[10px] text-gray-400 font-medium mt-0.5">(Inclusive of all taxes)</span>
                </div>
                """), unsafe_allow_html=True)
            with btn_col:
                if st.button("ADD TO CART", key=f"desktop_pdp_add_{sku_id}"):
                    add_to_cart(sku_id, name, price, category)
                    st.rerun()

            # Assurance & Warranty Badges
            if "cable" in name.lower() or "electronics" in category.lower():
                st.markdown("<div class='my-3'><span class='badge badge-warranty'>⚡ 6-Month Brand Warranty</span> <span class='badge badge-trust'>🔄 Easy 3-Day Replacement</span></div>", unsafe_allow_html=True)
            elif "sunscreen" in name.lower() or "beauty" in category.lower():
                st.markdown("<div class='my-3'><span class='badge badge-trust'>🔬 Dermatologically Tested</span> <span class='badge badge-trust'>🌿 100% Vegan & Non-Toxic</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='my-3'><span class='badge badge-trust'>🛡️ 100% Quality Guaranteed</span> <span class='badge badge-trust'>🔄 Easy Returns</span></div>", unsafe_allow_html=True)

            # "Why shop from blinkit?" section
            st.markdown(textwrap.dedent("""
            <div class="mt-4 pt-4 border-t border-gray-100 bg-white p-4 rounded-2xl border border-gray-100">
                <h4 class="font-outfit font-bold text-sm text-gray-900 mb-3">Why shop from blinkit?</h4>
                <div class="space-y-3">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-amber-100/80 flex items-center justify-center shrink-0">
                            <span class="text-sm">🚴</span>
                        </div>
                        <div>
                            <p class="font-bold text-xs text-gray-900">Round The Clock Delivery</p>
                            <p class="text-[10px] text-gray-500 leading-snug">Get items delivered to your doorstep from dark stores near you.</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-yellow-100/80 flex items-center justify-center shrink-0">
                            <span class="text-sm">💰</span>
                        </div>
                        <div>
                            <p class="font-bold text-xs text-gray-900">Best Prices & Offers</p>
                            <p class="text-[10px] text-gray-500 leading-snug">Best price destination with offers directly from manufacturers.</p>
                        </div>
                    </div>
                </div>
            </div>
            """), unsafe_allow_html=True)

        with pdp_col2:
            # Product Specifications & Details Card
            st.markdown(textwrap.dedent(f"""
            <div class="mb-4 bg-white p-5 rounded-2xl border border-gray-200 shadow-xs">
                <h3 class="font-outfit text-base font-bold text-gray-900 mb-2 border-b border-gray-100 pb-2">Full Specifications & Details</h3>
                <div class="space-y-2 text-xs text-gray-700">
                    <p class="text-gray-600 leading-relaxed text-xs">Authentic premium {name} prepared under hygienic conditions. Checked and packed to preserve freshness and nutrition for daily household consumption.</p>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-gray-100 text-xs">
                        <div>
                            <span class="text-gray-400 block font-medium">Category</span>
                            <span class="font-bold text-gray-800">{category}</span>
                        </div>
                        <div>
                            <span class="text-gray-400 block font-medium">Origin</span>
                            <span class="font-bold text-gray-800">India</span>
                        </div>
                        <div>
                            <span class="text-gray-400 block font-medium">Shelf Life</span>
                            <span class="font-bold text-gray-800">6 Months</span>
                        </div>
                        <div>
                            <span class="text-gray-400 block font-medium">Seller</span>
                            <span class="font-bold text-gray-800">Blinkit Pvt Ltd</span>
                        </div>
                    </div>
                </div>
            </div>
            """), unsafe_allow_html=True)

            # Evidence Gate similarity evaluation & Ratings Header
            query_text = "lightweight fast charging non sticky long durability"
            t0 = time.perf_counter()
            fallback_active, reviews, meta = router.run_evidence_gate(
                sku_id=sku_id,
                query_text=query_text,
                similarity_threshold=st.session_state.evidence_threshold
            )
            st.session_state.latency_metrics["vector_db"] = (time.perf_counter() - t0) * 1000

            top_stars = stars_html(base_rating)
            st.markdown(textwrap.dedent(f"""
            <div style="background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%); padding: 16px 20px; border-radius: 16px; border: 1px solid #fef3c7; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 6px rgba(245,158,11,0.05);">
                <div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                        {top_stars}
                        <span style="font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 900; color: #0f172a;">{base_rating} out of 5</span>
                    </div>
                    <p style="font-size: 12px; color: #475569; font-weight: 600; margin: 0; display: flex; align-items: center; gap: 6px;">
                        <span style="color: #0C831F; font-weight: 800;">✓ Verified</span> {review_count}+ buyers in DLF Phase 3 rated this product
                    </p>
                </div>
                <div style="background: #0C831F; color: white; padding: 6px 14px; border-radius: 10px; font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 900; box-shadow: 0 2px 6px rgba(12,131,31,0.2);">
                    ★ {base_rating:.1f} / 5.0
                </div>
            </div>
            """), unsafe_allow_html=True)

            # Verified Customer Reviews
            sample_reviews = get_sample_customer_reviews(name, category)
            st.markdown(textwrap.dedent(f"""
            <div style="background: white; padding: 20px; border-radius: 16px; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <h4 style="font-family: 'Outfit', sans-serif; font-size: 15px; font-weight: 800; color: #0f172a; margin: 0 0 14px 0;">Customer Reviews & Ratings</h4>
                {render_customer_reviews_html(sample_reviews)}
            </div>
            """), unsafe_allow_html=True)
    else:
        st.markdown("---")

    # --- SEARCH / FILTER RESULTS PANEL ---
    if (is_searching or is_filtering) and not is_pdp_active:
        st.markdown(textwrap.dedent(f"""
        <div class="border-b border-gray-200 pb-2 mb-6">
        <h2 class="font-outfit text-2xl font-bold text-gray-800">Results for '{search_q or st.session_state.active_category}'</h2>
        </div>
        """), unsafe_allow_html=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = "SELECT sku_id, name, price, category, base_rating FROM sku_catalog"
        params = []
        
        if is_filtering:
            query += " WHERE category = ?"
            params.append(st.session_state.active_category)
            if is_searching:
                query += " AND name LIKE ?"
                params.append(f"%{search_q}%")
        elif is_searching:
            query += " WHERE name LIKE ?"
            params.append(f"%{search_q}%")
            
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        if results:
            grid_col1, grid_col2 = st.columns(2)
            for idx, item in enumerate(results):
                sku_id, name, price, category, rating = item
                image_url = get_product_image_url(sku_id, name)
                
                target_col = grid_col1 if idx % 2 == 0 else grid_col2
                with target_col:
                    st.markdown(
                        render_product_card_html(
                            sku_id, image_url, name, price, category, "1 Unit • 8 mins"
                        ),
                        unsafe_allow_html=True,
                    )
                    if st.button("+ ADD 🛒", key=f"srch_add_{sku_id}", use_container_width=True):
                        add_to_cart(sku_id, name, price, category)
                        st.rerun()
        else:
            st.info("No matching products found. Try another search query!")
            
        if st.button("← Back to Landing"):
            st.session_state.active_category = "All"
            st.rerun()

    # --- STANDARD LANDING HOME PAGE FEED ---
    if not is_searching and not is_filtering and not is_pdp_active:
        banner_cols = st.columns(4)
        banners_data = [
            {
                "title": "Idols & Pooja Needs",
                "sub": "Festive Ready",
                "bg": "#FDFAE6",
                "border": "#FBF2CC",
                "text_color": "#725c00",
                "img": "https://lh3.googleusercontent.com/aida-public/AB6AXuAea1giejbX5RFFtoT7CgqqHZAa1TZCWBI4G_HRFdwvDxz0kDrRhHTAsttrjBHpzdYdHBfpXRSD00kh8WflZyE6erW1BV-JYFfGMkzrs8IdTo9PNqKTdNCxLgwQED7WvDtPOgWF-3XLEeXXi2vfTel-K-aMHAYYa6T03EBOx1wW-g945nGnGQGhF_vKnef1J5P3nmIplm1ongSDvij_hOk24G0VW5DzaK_Bo01i_1xqKDi4ZCZ6XoWm",
            },
            {
                "title": "Modaks & Sweets",
                "sub": "Fresh local prep",
                "bg": "#FFF0F6",
                "border": "#FFDEEB",
                "text_color": "#B01B5E",
                "img": "https://lh3.googleusercontent.com/aida-public/AB6AXuAKmJbpX93XHzSdnS1JFgYyz5C6wPADWYYBSrp9kT26Aig93_lf5pHY-KG0eh8HvC2obVQPREOotBa7EUpENTMrq5uJROEgwYvb5YFnb_LV0JkL18kdua3a4IoJGTHGmRtUl-ojoPi0m2axTNEP2Km_shXGrke8UkZXzCazO-6-piu9CsVyk4b20rTEXDamKFDaJEn9v-eYW7obU7QiFzFdGt0QlFzPBKSAzChhBo2oQudpL5Hmh1Mx",
            },
            {
                "title": "Home Decor",
                "sub": "Garlands & DIYAs",
                "bg": "#F4FBF7",
                "border": "#D3F9E8",
                "text_color": "#006d38",
                "img": "https://lh3.googleusercontent.com/aida-public/AB6AXuA1RkeIvxsfnwliwvVuUyP8yQWs7nBj3CgZlgMejXn4bzE3QvkaG_7Fuq-6vv16C86ixA2zNMN_7J4DLQy0saQAuRDOp3E_oPVAW8FAgaGghD0-ZRx2XVaomoPf7w6ELPr_-C3nKmws51Jl6tMps61ZjG-a-ASbov3CDQqqIejh8XdCjuykg3Ru1ZAEDiRJOTX5zqilxH2fmVWSHUliHoy9MOWBZpJVyz12If9J2ZNT8bS5BxCo__1S",
            },
            {
                "title": "Local Skincare",
                "sub": "SPF & Creams",
                "bg": "#E8F4FD",
                "border": "#D0EBFF",
                "text_color": "#0056D2",
                "img": "https://lh3.googleusercontent.com/aida-public/AB6AXuCMuXhlY-r3WZBzjPM3LRV65zTet8cTBJaGcfDeQX7q7CHKVkz_ZYgO0J8_bkhKu1wf9vQaHjPXOZMIEYZbpzPgnuzJZWrDrZFBw1wETD0-2qVuFsDuBaRUmKGOyji4pon2FsOyE1x_GeFyu0tY7np3KceISbjj0HmFppJ6vEgNvruz9Sa5hjedalFCRUytrTOwVnP5lqT-LOigxKvcw1kyCzhOtd0Q0rw1GQxB_ejzSLrwDHsnAyLB",
            }
        ]
        
        for idx, b in enumerate(banners_data):
            with banner_cols[idx]:
                st.markdown(textwrap.dedent(f"""
                <div style="background-color: {b['bg']}; border: 1px solid {b['border']}; border-radius: 16px; padding: 16px; height: 180px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center;" class="hover:shadow-lg transition-all mb-3">
                    <div>
                        <span style="color: {b['text_color']}; font-weight: 700; font-size: 15px; display: block; line-height: 1.2;" class="font-outfit">{b['title']}</span>
                        <span style="color: #888; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-top: 4px;">{b['sub']}</span>
                    </div>
                    <img src="{b['img']}" style="height: 64px; width: 64px; object-fit: contain; margin-top: 8px;">
                </div>
                """), unsafe_allow_html=True)

        st.markdown(textwrap.dedent("""
        <div class="border-b border-gray-200 pb-2 mb-6 mt-10">
        <h3 class="font-outfit text-xl font-bold text-gray-800">Frequently bought</h3>
        </div>
        """), unsafe_allow_html=True)

        staples = [
            {"sku_id": "SKU-STAPLE-COFFEE", "name": "Premium Coffee Beans", "price": 450.0, "cat": "Grocery"},
            {"sku_id": "SKU-STAPLE-WASH", "name": "Foaming Face Wash", "price": 299.0, "cat": "Beauty/Skincare"},
            {"sku_id": "SKU-STAPLE-MILK", "name": "Organic Whole Milk 1L", "price": 75.0, "cat": "Grocery"},
        ]
        
        staples_c1, staples_c2, staples_c3 = st.columns(3)
        for idx, s in enumerate(staples):
            target_c = [staples_c1, staples_c2, staples_c3][idx]
            img = get_product_image_url(s["sku_id"], s["name"])
            with target_c:
                st.markdown(
                    render_product_card_html(
                        s["sku_id"], img, s["name"], s["price"], s["cat"], "1 Unit • 8 mins"
                    ),
                    unsafe_allow_html=True,
                )
                if st.button("+ ADD 🛒", key=f"stp_add_{s['sku_id']}", use_container_width=True):
                    add_to_cart(s["sku_id"], s["name"], s["price"], s["cat"])
                    st.rerun()

# --- DESKTOP WEB FOOTER ---
st.markdown(textwrap.dedent("""
<footer class="bg-white border-t border-gray-100 py-16 px-12 mt-20">
<div class="max-w-[1440px] mx-auto grid grid-cols-1 md:grid-cols-4 gap-12 text-sm text-gray-600 font-medium">
<div class="space-y-4">
<h2 class="font-outfit text-3xl font-black text-gray-900 tracking-tighter">Blinkit</h2>
<p class="leading-relaxed">Delivering freshness to your doorstep in under 10 minutes. DLF Phase 3's favorite quick commerce partner.</p>
</div>
<div class="space-y-4">
<p class="font-outfit text-xs font-bold text-gray-800 uppercase tracking-widest">Categories</p>
<ul class="space-y-2 text-xs">
<li><a class="hover:text-[#006d38] transition-colors" href="#">Groceries & Staples</a></li>
<li><a class="hover:text-[#006d38] transition-colors" href="#">Fruits & Vegetables</a></li>
<li><a class="hover:text-[#006d38] transition-colors" href="#">Personal Care</a></li>
<li><a class="hover:text-[#006d38] transition-colors" href="#">Home Needs</a></li>
</ul>
</div>
<div class="space-y-4">
<p class="font-outfit text-xs font-bold text-gray-800 uppercase tracking-widest">Support</p>
<ul class="space-y-2 text-xs">
<li><a class="hover:text-[#006d38] transition-colors" href="#">Help Center</a></li>
<li><a class="hover:text-[#006d38] transition-colors" href="#">Refund Policy</a></li>
<li><a class="hover:text-[#006d38] transition-colors" href="#">Contact Us</a></li>
</ul>
</div>
<div class="space-y-4">
<p class="font-outfit text-xs font-bold text-gray-800 uppercase tracking-widest">Experience</p>
<div class="flex gap-3">
<span class="inline-block px-4 py-2 bg-black text-white text-xs rounded-lg font-bold cursor-pointer">App Store</span>
<span class="inline-block px-4 py-2 bg-black text-white text-xs rounded-lg font-bold cursor-pointer">Play Store</span>
</div>
</div>
</div>
</footer>
"""), unsafe_allow_html=True)
