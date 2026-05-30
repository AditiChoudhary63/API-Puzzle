# Submitted Responses

## Layer 1 — Content Hash

**Endpoint:** `POST /api/v1/submit`

**Request:**
```json
{
  "type": "content_hash",
  "value": "08631675d7811b85c7f1562983c857e4f090c13c3a433dbc9d7f51f303b7e692"
}
```

**Response:**
```json
{
  "correct": true,
  "layer": 1,
  "message": "Correct!",
  "submission_id": "ba5d9e25-1f2c-47f2-8519-318fa4261498",
  "type": "content_hash"
}
```

---

## Layer 2 — Decrypted Hash

**Endpoint:** `POST /api/v1/submit`

**Request:**
```json
{
  "type": "decrypted_hash",
  "value": "f0d7366fbb3aa0190e54709f03ffe672ee10cc208eea62c0631237f4b01601ab"
}
```

**Response:**
```json
{
  "correct": true,
  "layer": 2,
  "message": "Correct!",
  "submission_id": "0abb081f-8401-41e2-aae5-bc71244697ac",
  "type": "decrypted_hash"
}
```

---

## Transcript

**Endpoint:** `POST /api/v1/submit`

**Request:**
```json
{
  "type": "transcript",
  "value": "analytics"
}
```

**Response:**
```json
{
  "correct": true,
  "layer": null,
  "message": "Correct!",
  "submission_id": "b0efbbec-bb3c-42d8-a237-d33f5c445b1c",
  "type": "transcript"
}
```
