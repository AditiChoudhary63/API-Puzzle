"""
Layer 2 — Decrypt the dataset using the RSA private key issued by the platform.

Key endpoint : GET /api/v1/private-key  (returns PEM, no auth required)
Cipher       : RSA-2048 / PKCS#1 v1.5
Each record  : 256 bytes of ciphertext (base64-encoded in the dataset)
Integrity    : SHA-256 of all decrypted plaintext bytes concatenated in order.
"""

import base64
import hashlib
import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

load_dotenv(Path(__file__).parents[1] / ".env")

BASE_URL = os.environ["BASE_URL"]
API_KEY  = os.environ["API_KEY"]
HEADERS  = {"Authorization": f"Bearer {API_KEY}"}


def fetch_private_key() -> RSA.RsaKey:
    """Fetch the RSA private key from the platform."""
    resp = requests.get(f"{BASE_URL}/api/v1/private-key", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return RSA.import_key(resp.text)


def decrypt_records(records: list[str], key: RSA.RsaKey) -> list[bytes]:
    cipher = PKCS1_v1_5.new(key)
    decrypted = []
    for i, rec in enumerate(records):
        plaintext = cipher.decrypt(base64.b64decode(rec), sentinel=None)
        if plaintext is None:
            raise ValueError(f"Decryption failed for record {i}")
        decrypted.append(plaintext)
    return decrypted


def decrypted_hash(plaintexts: list[bytes]) -> str:
    """SHA-256 of all plaintext bytes concatenated in order."""
    return hashlib.sha256(b"".join(plaintexts)).hexdigest()


if __name__ == "__main__":
    # Load encrypted dataset (produced by layer1.py)
    dataset_path = Path("dataset.json")
    if not dataset_path.exists():
        print("dataset.json not found — run layer1.py first.")
        raise SystemExit(1)

    records = json.loads(dataset_path.read_text())
    print(f"Loaded {len(records)} encrypted records")

    print("Fetching RSA private key from /api/v1/private-key ...")
    private_key = fetch_private_key()
    print("Key loaded — decrypting ...")

    plaintexts = decrypt_records(records, private_key)
    print(f"Decrypted {len(plaintexts)} records")

    # Save decrypted records as JSON strings
    decoded = [p.decode("utf-8") for p in plaintexts]
    Path("decrypted.json").write_text(json.dumps(decoded, indent=2))
    print("Saved plaintext records to decrypted.json")

    digest = decrypted_hash(plaintexts)
    print(f"\nDecrypted hash : {digest}")
    print("\nSubmit via:")
    print(f'  POST /api/v1/submit  {{"type":"decrypted_hash","value":"{digest}"}}')
