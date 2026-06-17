# API Puzzle — Aditi Choudhary

Solution to the four-layer engineering API Puzzle

## Repository structure

```
.
├── .env                          # BASE_URL + API_KEY (not committed)
├── .gitignore
├── requirements.txt
├── solution/
│   ├── layer1.py                 # Layer 1 — fetch & integrity hash
│   ├── layer2.py                 # Layer 2 — RSA decrypt & hash
│   ├── layer3.py                 # Layer 3 — hidden answer
│   ├── layer4.py                 # Layer 4 — free-form analysis
│   ├── dataset.json              # Cached encrypted ciphertext (500 records)
│   ├── decrypted.json            # Cached plaintext records (500 records)
│   └── submitted_responses.md   # All submission requests + API responses
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the repo root:

```
BASE_URL = https://<your-base-url>
API_KEY  = sa_<your-key>
```

## Running the layers

All scripts are run from the `solution/` directory (or the repo root — they resolve paths relative to their own location).

### Layer 1 — Content hash

Downloads the full 500-record encrypted dataset in 5 batches of 100, computes SHA-256 of the concatenated raw ciphertext bytes, and prints the hash to submit.

```bash
python solution/layer1.py
```

Output cached to `solution/dataset.json` on first run; subsequent runs load from cache.

### Layer 2 — Decrypt and hash

Fetches the RSA-2048 private key from `GET /api/v1/private-key`, decrypts all 500 records using PKCS#1 v1.5, and computes SHA-256 of the concatenated plaintext bytes.

```bash
python solution/layer2.py
```

Requires `solution/dataset.json` (produced by Layer 1). Decrypted records saved to `solution/decrypted.json`.

### Layer 3 — Hidden answer

```bash
python solution/layer3.py
```

### Layer 4 — Free-form analysis

Statistical analysis of the decrypted API log dataset covering error rates, latency, method distribution, and anomaly detection.

```bash
python solution/layer4.py
```

## Key findings (Layer 4)

- **69.6% error rate** — system is severely degraded (normal: <5%)
- **401 Unauthorized** is the #1 status code — auth failures dominate
- `partner` segment generates **19.8% of all traffic** (99/500), ~2× any other segment
- `partner` accounts for **38% of all auth/refresh calls** — a token-refresh loop signature
- `GET` is the **least common HTTP method** — `DELETE`/`PUT` dominate (automated/bot behaviour)
- `orders` endpoint has the highest error rate at **77.6%** — checkout is broken
- **69 semantically nonsensical calls** (e.g. `DELETE /auth/login`, `PUT /auth/refresh`); `partner` alone accounts for 21

**Conclusion:** The dataset depicts a compromised API environment where a rogue `partner` integration is conducting persistent automated credential attacks (primarily token-refresh abuse), while commerce-critical endpoints (`orders` 77.6%, `billing` 72.5%) degrade and the overall success rate sits at only 30%.

## Submitted answers

| Layer | Type | Correct |
|-------|------|---------|
| 1 | `content_hash` | ✓ |
| 2 | `decrypted_hash` | ✓ |
| 3 | (in progress) | — |
| 4 | Free-form analysis | accepted |

Full request/response pairs are documented in [`solution/submitted_responses.md`](solution/submitted_responses.md).

## Technical approach

| Concern | Decision |
|---------|----------|
| Dataset download | 5 × 100-record batches with retry on 429/5xx; result cached locally |
| Encryption | RSA-2048 / PKCS#1 v1.5 via `pycryptodome`; key fetched live from `/api/v1/private-key` |
| Integrity hashes | SHA-256 of raw bytes concatenated in dataset order (ciphertext for L1, plaintext for L2) |
| Credentials | `BASE_URL` + `API_KEY` loaded from `.env` via `python-dotenv`; never committed |
