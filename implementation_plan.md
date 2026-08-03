# Implementation Plan: AI-Powered Contextual Trust & Hyper-Local Discovery Engine

This document outlines the step-by-step implementation plan for building the Blinkit MVP application. It breaks down the system development into distinct, actionable phases, complete with verification steps for each phase to ensure reliability and speed (sub-200ms recommendation latency).

---

## Phase 1: Environment Setup & Synthetic Data Ingestion
**Goal**: Establish the repository framework, install core dependencies, and ingest raw synthetic datasets representing customer behavior in **DLF Phase 3, Gurugram**.

### Tasks
1. Initialize the project workspace structure.
2. Create `requirements.txt` containing the necessary dependencies:
   - `streamlit` (UI framework)
   - `chromadb` (vector storage)
   - `groq` (LLM inference client)
   - `pandas`, `numpy` (data handling)
   - `sentence-transformers` (local embeddings fallback) or `openai` (remote embeddings)
   - `datasketch` (for MinHash deduplication)
3. Generate synthetic data files in `data/`:
   - `raw_reviews.json`: 3 months of customer feedback for apparel, beauty/skincare, and electronics.
   - `order_history.json`: Transaction logs showing item co-occurrences (e.g., Face Wash + Sunscreen).
4. Implement the **Deduplication & Cleaning Pipeline** (`src/pipeline.py`):
   - Deduplication utilizing MinHash LSH.
   - Regular expression-based PII scrubber (phone, email, names).
   - Language parser to clean English and Hinglish content.

### Verification
* Run the pipeline script to verify clean outputs are generated in `data/cleaned_reviews.json`.
* Assert that duplicate entries are reduced and PII is properly masked.

---

## Phase 2: Vector Indexing & Co-occurrence Storage
**Goal**: Generate dense vector embeddings for the cleaned feedback data and establish the relational databases.

### Tasks
1. Implement the embedding script (`src/embedder.py`) to encode text reviews into dense vectors using `bge-small-en-v1.5` or `text-embedding-3-small`.
2. Configure **ChromaDB** to store vectors locally under an HNSW index.
3. Construct a SQLite database (`data/blinkit_local.db`) with tables:
   - `co_occurrences`: Mapping primary staples to non-grocery add-ons, with transaction counts and prices.
   - `sku_catalog`: Item metadata (price, category, standard ratings).
4. Populated SQLite with aggregated data parsed from `order_history.json`.

### Verification
* Run vector DB search queries on target SKUs and check that returned documents have similarity scores.
* Query SQLite tables to confirm co-occurrence counts and prices ($< \text{₹}199$) return correctly.

---

## Phase 3: Integration Layer & "Evidence Gate" Protocol
**Goal**: Build the middleware logic that handles retrieval, filters semantic matches, and applies safety logic.

### Tasks
1. Write the **Integration Layer Router** (`src/integration.py`) to orchestrate queries to ChromaDB and SQLite when a user interacts with a SKU or updates their cart.
2. Implement the **Evidence Gate** algorithm:
   - Retrieve nearest neighbor reviews.
   - Compute cosine similarity score $S$.
   - **Condition**: Filter where $S \ge 0.90$. If matching count $< 2$, trigger `fallback_mode = True`.
3. Create the **Add-On Ranker**:
   - Given a staple item in the cart, fetch associated items from the co-occurrence matrix.
   - Filter items where `price < 199` and category is non-grocery.
   - Sort by co-occurrence strength (number of times bought together).

### Verification
* Unit test the Evidence Gate: Mock reviews with $S = 0.95$ and $S = 0.85$. Verify that only $S \ge 0.90$ pass.
* Verify that if fewer than 2 reviews pass, `fallback_mode` evaluates to `True`.

---

## Phase 4: Groq Trust Engine Integration
**Goal**: Implement the LLM inference client to synthesize reviews and extract verbatim quotes.

### Tasks
1. Set up the Groq Cloud API connection utilizing `llama-3.3-70b-versatile`.
2. Design the prompt templates in `src/prompts.py`:
   - System prompts enforcing the 2-line summary limit.
   - Constraints requiring exactly 2 verbatim sentences from the source reviews.
   - Instruction to format output strictly as a JSON object.
3. Write the **Trust Engine Service** (`src/trust_engine.py`):
   - Accepts passed reviews from the Evidence Gate.
   - Queries Groq.
   - Parses the JSON response.
   - Implements error handling and a timeout threshold (e.g., if Groq takes $> 150\text{ms}$, return static fallbacks).

### Verification
* Send sample reviews to the service and print the JSON output.
* Verify that the summary is exactly 2 lines and quotes are exact matches of the input reviews.

---

## Phase 5: Streamlit Mobile-Simulation UI
**Goal**: Develop the interactive frontend representing Blinkit’s 7-step quick-commerce checkout.

### Tasks
1. Build the Streamlit layout (`app.py`) designed with a mobile viewport aspect ratio (similar to a smartphone screen).
2. Code the simulated **7-Step Checkout Journey Stepper** navigation.
3. Implement the interface components:
   - **Product Display Page (PDP)**: Surfaces star rating badge, RAG-generated summary (or fallback rating text), and assurance badges (e.g., `⚡ Warranty`).
   - **Cart Drawer**: A sidebar or drawer slide-out showing added items.
   - **Recommendation Carousel**: Displays neighbor-validated cart add-ons (e.g., *"⚡ 120+ neighbors in DLF Phase 3 bought this"*).
   - **Smart Cart-Filler Bar**: Banner prompting users to add small items under ₹199 to unlock rewards/free shipping.

### Verification
* Launch Streamlit locally (`streamlit run app.py`).
* Interact with the simulated journey steps and verify correct component rendering on PDP and Cart screens.

---

## Phase 6: Latency Optimization & Final Verification
**Goal**: Optimize execution paths, measure latency metrics, and write the walkthrough documentation.

### Tasks
1. Implement a **latency tracker** decorator to measure execution times of DB queries, LLM calls, and render loops.
2. Set up local caching utilizing `streamlit.cache_data` or a memory cache (e.g., `dict` or `Redis`) for SKU vectors and common co-occurrences.
3. Run stress-testing to verify latency:
   - Target: Average latency for recommendation payloads **$< 200\text{ms}$**.
4. Generate the final walkthrough showing screenshots of the application working under both normal and fallback modes.

### Verification
* Output logs showing execution times for each integration layer step.
* Confirm that simulated network or Groq failures correctly route to fallback logic with no UI freezes.
