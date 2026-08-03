# Edge Cases & Corner Cases Analysis

This document identifies potential edge cases, system vulnerabilities, and corner cases for the AI-Powered Contextual Trust & Hyper-Local Discovery Engine. It outlines concrete mitigation strategies and automated testing scenarios to ensure the system remains resilient and achieves sub-200ms latency under all conditions.

---

## 1. Data Ingestion & Preprocessing Edge Cases

### 1.1. High-Density PII & Blank Reviews
* **Case**: Reviews containing *only* PII (e.g., `"Contact me at 9876543210 for details"`) or composed entirely of emojis/punctuation (e.g., `"!!! 👍👍"`).
* **Impact**: Scrubbing PII results in empty text, causing indexing failures or semantic embedding of whitespace.
* **Mitigation**:
  - Implement a minimum length threshold (e.g., $\ge 15$ characters after stripping punctuation and whitespace) before sending text to the embedding pipeline.
  - Skip vector database ingestion for empty/meaningless post-scrubbed texts.

### 1.2. Hinglish Sentiment Inversion
* **Case**: Code-mixed reviews where semantic meaning is inverted by subtle Hinglish words (e.g., `"Product was looking good but working bilkul bakwaas hai"`).
* **Impact**: English-trained embedding models (`bge-small-en-v1.5`) may map `"looking good"` to a positive vector, ignoring the negative Hinglish modifier `"bilkul bakwaas"` (entirely garbage).
* **Mitigation**:
  - Standardize vocabulary during text normalization (e.g., mapping `"bakwaas"` ➔ `"garbage/bad"`, `"mast"` ➔ `"great"`).
  - Benchmark embedding models with a dedicated Hinglish evaluation set to verify correct clustering of mixed-language sentiment.

### 1.3. MinHash LSH Near-Duplicate Collisions
* **Case**: Reviews that share high word co-occurrence but express opposing viewpoints (e.g., `"The product is bad, not good"` vs. `"The product is good, not bad"`).
* **Impact**: LSH deduplication might flag these as duplicates and discard one, losing crucial opposing feedback.
* **Mitigation**:
  - Run semantic similarity checks or sentiment comparison *before* discarding duplicate candidates, or limit deduplication to Jaccard similarity threshold $J \le 0.85$.

---

## 2. Vector DB & Evidence Gate ($S \ge 0.90$) Edge Cases

### 2.1. "Sparse Evidence" Scenarios
* **Case**: Target SKU has only one high-confidence review ($S \ge 0.90$), or many reviews with similarity scores just below the threshold (e.g., $S = 0.89$).
* **Impact**: Fails the Evidence Gate constraint (which requires $\ge 2$ matching reviews), causing a fallback.
* **Mitigation**:
  - Strictly enforce the transition to `fallback_mode` (no LLM summary, show aggregate ratings instead).
  - Dynamically log threshold failures to flag low-penetration SKUs that need organic review collection.

### 2.2. Valid Negative Social Proof
* **Case**: Target SKU has multiple reviews with similarity $S \ge 0.95$, but they are overwhelmingly negative (e.g., `"The fabric tore after one wash"`, `"Waste of money, poor stitching"`).
* **Impact**: Blindly generating a "trust summary" might lead the LLM to write a negative summary, hurting sales, or attempt to put a positive spin on a bad product, violating user trust.
* **Mitigation**:
  - **Negative Sentiment Gate**: Pre-evaluate the sentiment score of the candidate reviews. If average sentiment is negative, disable PDP summary cards entirely, or display a neutral comparison chart instead of an AI-generated praise summary.

---

## 3. Co-occurrence Matrix & Recommendation Edge Cases

### 3.1. Cold Start for New SKUs
* **Case**: A newly launched non-grocery item has zero transaction history in DLF Phase 3.
* **Impact**: The co-occurrence table return is empty, resulting in blank recommendation slots.
* **Mitigation**:
  - Fall back to global (cluster-level or city-level) co-occurrence data.
  - If no global co-occurrence data exists, recommend category-level bestsellers (e.g., top-selling items under Skincare) for DLF Phase 3.

### 3.2. Out-of-Stock Recommendations
* **Case**: A recommended filler item ($< \text{₹}199$) is out of stock in the DLF Phase 3 dark store.
* **Impact**: User tries to add the item via the one-tap filler bar, resulting in an "Out of Stock" error, creating frustration.
* **Mitigation**:
  - Integrate real-time stock levels into the recommendation filter database query:
    ```sql
    SELECT item_id FROM co_occurrences 
    INNER JOIN inventory ON item_id = inventory.sku_id
    WHERE inventory.stock_level > 0 AND price < 199;
    ```

### 3.3. Cart Boundary Conditions
* **Case**: The customer's cart value is exactly ₹198, and the free delivery threshold is ₹199.
* **Impact**: The system needs a ₹1 filler, but all recommended add-ons cost $\ge \text{₹}30$.
* **Mitigation**:
  - Design the Smart Cart-Filler Bar to handle the residual value gracefully. If the remaining gap is $< \text{₹}10$, prompt with the lowest available cost item (e.g., a ₹10 carry bag or ₹15 sachet) rather than expensive SKUs.

---

## 4. LLM (Groq API) & Latency SLA Edge Cases

### 4.1. Rate Limits & Service Outages (HTTP 429 / 500 / 503)
* **Case**: Groq API rate limits are exceeded during high-traffic checkout hours, or the Groq service encounters an outage.
* **Impact**: API requests fail, resulting in uncaught errors or long connection timeouts that block the UI.
* **Mitigation**:
  - Wrap Groq API calls in a `try-except` block with a tight network timeout (e.g., `timeout=0.15` seconds).
  - Catch all Groq exceptions and immediately route to the local cache or static aggregate metrics fallback.

### 4.2. JSON Schema Violation / Hallucinated Formats
* **Case**: Llama-3.3-70b-versatile returns its response wrapped in markdown backticks (e.g., ` ```json ... ``` `) or adds conversational text (e.g., `"Here is your summary:"`).
* **Impact**: `json.loads()` throws a parsing exception, crashing the PDP interface.
* **Mitigation**:
  - Enforce JSON mode on the Groq API configuration (`response_format={"type": "json_object"}`).
  - Implement a cleaning function to strip markdown syntax wrappers before parsing:
    ```python
    def clean_json_string(raw_response):
        raw_response = raw_response.strip()
        if raw_response.startswith("```json"):
            raw_response = raw_response[7:]
        if raw_response.endswith("```"):
            raw_response = raw_response[:-3]
        return raw_response.strip()
    ```

---

## 5. UI & State Management Edge Cases

### 5.1. Rapid Navigation (Double-Clicking / Thread Racing)
* **Case**: The user rapidly clicks "Add to Cart" or switches checkout steps before the previous recommendation API completes.
* **Impact**: Streamlit thread congestion, out-of-order state updates, or database lock errors.
* **Mitigation**:
  - Disable buttons or show loading skeletons during active execution.
  - Use Streamlit session state keys to track active API calls and discard outdated responses.
