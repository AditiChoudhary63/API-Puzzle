"""
Layer 1 — Fetch the full dataset and prove byte-level integrity.

Endpoint: GET /api/v1/dataset?batch=true&range=<start>-<end>
Strategy : 5 batch requests of 100 records each (rate limit: 5 req/s).
Integrity: SHA-256 of all raw ciphertext bytes concatenated in order.
"""

import hashlib
import json
import os
import time
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env")

BASE_URL = os.environ["BASE_URL"]
API_KEY  = os.environ["API_KEY"]
HEADERS  = {"Authorization": f"Bearer {API_KEY}"}


def fetch_batch(start: int, end: int) -> list[str]:
    """Fetch one batch of records; retries on 429 / 5xx."""
    url = f"{BASE_URL}/api/v1/dataset?batch=true&range={start}-{end}"
    for _ in range(10):
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 429:
            time.sleep(float(resp.headers.get("retry-after", 1)) + 0.1)
        elif resp.status_code in (500, 503):
            time.sleep(2)
        else:
            resp.raise_for_status()
            return resp.json()["data"]
    raise RuntimeError("Batch fetch failed after 10 attempts")


def download_dataset(cache_path: Path = Path("dataset.json")) -> list[str]:
    if cache_path.exists():
        print(f"Loading cached dataset from {cache_path}")
        return json.loads(cache_path.read_text())

    print("Downloading 500 records in 5 batches of 100 ...")
    records: list[str] = []
    for start in range(0, 500, 100):
        batch = fetch_batch(start, start + 99)
        records.extend(batch)
        print(f"  Fetched records {start}–{start + 99}  (total so far: {len(records)})")
        time.sleep(0.3)

    cache_path.write_text(json.dumps(records))
    print(f"Saved to {cache_path}")
    return records


def content_hash(records: list[str]) -> str:
    """SHA-256 of all raw ciphertext bytes concatenated in dataset order."""
    raw = b"".join(base64.b64decode(r) for r in records)
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    records = download_dataset()
    digest  = content_hash(records)
    print(f"\nDataset size : {len(records)} records")
    print(f"Content hash : {digest}")
    print("\nSubmit via:")
    print(f'  POST /api/v1/submit  {{"type":"content_hash","value":"{digest}"}}')
