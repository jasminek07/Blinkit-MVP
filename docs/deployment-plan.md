# Streamlit Cloud Deployment Plan — Blinkit MVP

This document outlines the step-by-step technical plan for deploying the **Blinkit Hyper-Local Commerce MVP** to **Streamlit Community Cloud** (or custom hosting environments).

---

## 1. Overview & Architecture Summary

- **Application File**: `app.py`
- **Deployment Platform**: Streamlit Community Cloud ([share.streamlit.io](https://share.streamlit.io))
- **Database Layer**: SQLite (`data/blinkit_local.db`) populated via `src/db_setup.py`
- **Vector Search Engine**: ChromaDB persistent client (`data/chroma_db`)
- **LLM Engine**: Groq API (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`)

---

## 2. Pre-Deployment Prerequisites

Before deploying to Streamlit Community Cloud, verify the following prerequisites:

1. **GitHub Repository**: Code pushed to a public or private GitHub repository.
2. **Groq API Key**: Obtain an active API key from [console.groq.com](https://console.groq.com/).
3. **Python Runtime**: Python `3.10` or `3.11` recommended.

---

## 3. Repository Structure & Configuration

Ensure your repository includes the following essential files:

```
Blinkit MVP/
├── app.py                      # Main Streamlit application entry point
├── requirements.txt            # Python package dependencies
├── docs/
│   └── deployment-plan.md      # Deployment guide
├── data/
│   ├── order_history.json      # Sample transaction data
│   └── cleaned_reviews.json    # Sample customer review data
└── src/
    ├── db_setup.py             # Database seed & setup script
    ├── integration.py          # Integration router & rec engine
    ├── trust_engine.py         # Evidence gate & LLM reasoning engine
    └── vector_store.py         # ChromaDB vector embedding wrapper
```

### Verified `requirements.txt`
```text
streamlit
chromadb
groq
pandas
numpy
sentence-transformers
datasketch
python-dotenv
```

---

## 4. Environment Secrets Setup

Streamlit Cloud uses a secure secrets manager (`.streamlit/secrets.toml`).

### Local Testing Secrets (`.streamlit/secrets.toml`)
Create a `.streamlit/secrets.toml` file locally:

```toml
GROQ_API_KEY = "gsk_your_groq_api_key_here"
```

### Streamlit Cloud Secrets Dashboard
When creating the app on Streamlit Cloud:
1. Navigate to **App Settings** → **Secrets**.
2. Paste your secret keys in TOML format:
```toml
GROQ_API_KEY = "gsk_your_groq_api_key_here"
```

---

## 5. Automated First-Boot Database Initialization

To ensure the SQLite catalog and ChromaDB vector store exist on Streamlit Cloud without manual SSH access, `app.py` automatically initializes missing database files on boot:

```python
import os
import subprocess

# Ensure SQLite and ChromaDB database directories exist on cloud startup
if not os.path.exists("data/blinkit_local.db"):
    print("Database missing. Initializing database and ChromaDB vector index...")
    subprocess.run(["python3", "src/db_setup.py"], check=True)
```

---

## 6. Step-by-Step Streamlit Cloud Deployment Guide

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Prepare repository for Streamlit Cloud deployment"
git push origin main
```

### Step 2: Create App on Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click the **"New app"** button.
3. Select your GitHub repository, set branch to `main`, and main file path to `app.py`.
4. (Optional) Customize your app URL (e.g., `blinkit-mvp.streamlit.app`).

### Step 3: Add API Secrets
1. Click **"Advanced settings..."** before deploying (or go to **Settings > Secrets** post-launch).
2. Paste your `GROQ_API_KEY`.
3. Click **Save**.

### Step 4: Deploy App
1. Click **"Deploy!"**.
2. Streamlit Cloud will build the container, install dependencies from `requirements.txt`, initialize database artifacts, and launch `app.py`.

---

## 7. Post-Deployment Verification Checklist

Once deployed, perform the following verification steps:

- [ ] **Catalog Grid Rendering**: Verify all products (Milk, Bread, Coffee, Sunscreen, Fast Charging Cable, Scrunchies, Socks) render with standardized `110px x 110px` images.
- [ ] **Cart Drawer**: Click "+ ADD" on any product and verify the right-side sliding overlay drawer opens automatically.
- [ ] **Category-Matched Recommendations**: Add a Grocery item and verify that recommended cross-sells are strictly same-category Grocery items.
- [ ] **Hyper-Local Indian Social Proof**: Check that cart recommendation badges display authentic Indian neighbor tags (e.g., `⚡ Saksham from 1km distance also ordered...`).
- [ ] **PDP & Bright Yellow Stars**: Open a product page and verify Customer Reviews display bright golden yellow (`#FFB800`) stars.

---

## 8. Troubleshooting & Performance Optimization

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError` | Missing package in `requirements.txt` | Add package name to `requirements.txt` and push to GitHub. |
| `Groq API Key Missing` | Secret not declared in Dashboard | Add `GROQ_API_KEY` under App Settings → Secrets. |
| Memory Limit Exceeded (Resource Limit) | Large SentenceTransformer model in memory | Use PyTorch CPU-only build or lightweight embeddings (`all-MiniLM-L6-v2`). |
| Database Lock Error | Concurrent SQLite writes | Ensure connections use `conn.close()` immediately after read queries. |

---

## 9. Conclusion

Following this deployment plan ensures a smooth, robust, and automated zero-downtime deployment of the **Blinkit MVP** application on Streamlit Community Cloud.
