import json
import os
import re

# Helper: Tokenize text into word unigrams
def get_shingles(text):
    # Normalize and split into words
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    return set(words)

# Pure Python MinHash signature generator
class MinHasher:
    def __init__(self, num_hashes=64):
        self.num_hashes = num_hashes
        # Create a set of seeds for reproducible hashing
        self.seeds = [i * 37 + 17 for i in range(num_hashes)]

    def compute_signature(self, shingles):
        signature = []
        if not shingles:
            return [float('inf')] * self.num_hashes
        
        for seed in self.seeds:
            min_val = float('inf')
            for shingle in shingles:
                # Stable hash using string combination
                h_val = hash(f"{seed}_{shingle}")
                if h_val < min_val:
                    min_val = h_val
            signature.append(min_val)
        return signature

    def compute_similarity(self, sig1, sig2):
        matches = sum(1 for x, y in zip(sig1, sig2) if x == y)
        return matches / self.num_hashes

# PII Scrubber
def scrub_pii(text):
    # Scrub emails
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    text = re.sub(email_pattern, "<REDACTED_EMAIL>", text)

    # Scrub phone numbers (10 digits, possibly with +91, spaces or hyphens)
    phone_pattern = r'(?:\+91[\-\s]?)?[6-9]\d{9}|\b\d{5}[\-\s]?\d{5}\b'
    text = re.sub(phone_pattern, "<REDACTED_PHONE>", text)

    # Scrub specific addresses (Sector, DLF Phase, House details)
    address_patterns = [
        r'\b(?:house|flat|h\.no|hno)\s*\w*(?:,\s*\w+)*\b',
        r'\bsector\s*\d+\b',
        r'\bdlf\s*phase\s*\d+\b'
    ]
    for pattern in address_patterns:
        text = re.sub(pattern, "<REDACTED_ADDRESS>", text, flags=re.IGNORECASE)

    # Clean up double spaces or trailing punctuation due to redaction
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Language Normalizer & Cleaner
def clean_text(text):
    # Normalize punctuation, keep common Hinglish expressions
    # Strip non-standard characters but preserve Hinglish characters, basic symbols, and redaction angle brackets
    text = re.sub(r'[^\w\s\.\,\!\?\-\@\#\$\%\★\☆\<\>]', '', text)
    return text.strip()

def run_cleaning_pipeline(input_path, output_path):
    print(f"Reading raw reviews from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    minhasher = MinHasher(num_hashes=64)
    processed_reviews = []
    signatures = []

    duplicate_count = 0

    for review in reviews:
        raw_text = review.get("review_text", "")
        
        # 1. Clean and scrub text
        scrubbed = scrub_pii(raw_text)
        cleaned = clean_text(scrubbed)
        
        # 2. Extract shingles and compute signature
        shingles = get_shingles(cleaned)
        sig = minhasher.compute_signature(shingles)
        
        # 3. Check for duplicates in already processed reviews using MinHash Jaccard similarity
        is_duplicate = False
        for idx, prev_sig in enumerate(signatures):
            sim = minhasher.compute_similarity(sig, prev_sig)
            # If similarity is >= 0.85 and they are for the same SKU, mark as duplicate
            if sim >= 0.85 and processed_reviews[idx]["sku_id"] == review["sku_id"]:
                is_duplicate = True
                break
        
        if is_duplicate:
            duplicate_count += 1
            print(f"Discarding duplicate review: {review['review_id']} for SKU: {review['sku_id']}")
            continue
        
        # 4. If unique, add to lists
        updated_review = review.copy()
        updated_review["review_text"] = cleaned
        processed_reviews.append(updated_review)
        signatures.append(sig)

    print(f"Ingested {len(reviews)} reviews. Discarded {duplicate_count} duplicates. Retained {len(processed_reviews)} unique reviews.")

    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_reviews, f, indent=2)
    print(f"Cleaned reviews saved successfully to {output_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, "data", "raw_reviews.json")
    output_file = os.path.join(base_dir, "data", "cleaned_reviews.json")
    run_cleaning_pipeline(input_file, output_file)
