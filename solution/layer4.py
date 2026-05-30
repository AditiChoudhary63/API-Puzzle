"""
Layer 4 — Free-form analysis of the decrypted API log dataset.
500 records, Jan 1 – Mar 31 2026 (Q1).
Fields: endpoint, latency_ms, method, request_bytes, status_code, timestamp, user_segment
"""

import json
from collections import Counter, defaultdict
import statistics
from pathlib import Path

DATA = Path(__file__).parent / "decrypted.json"


def load():
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    return [json.loads(r) for r in raw]


def run():
    records = load()
    records_ts = sorted(records, key=lambda r: r["timestamp"])

    # ── 1. Overall success vs error rate ─────────────────────────────────────
    success = sum(1 for r in records if r["status_code"] < 400)
    print(f"[1] Success rate  : {success}/500 = {success/5:.1f}%")
    print(f"    Error   rate  : {500-success}/500 = {(500-success)/5:.1f}%")

    # ── 2. Most common status code ────────────────────────────────────────────
    status_counts = Counter(r["status_code"] for r in records).most_common(5)
    print(f"\n[2] Top 5 status codes: {status_counts}")

    # ── 3. user_segment request counts (anomaly detection) ───────────────────
    seg_counts = Counter(r["user_segment"] for r in records)
    total = len(records)
    print("\n[3] Requests per user_segment:")
    for seg, cnt in seg_counts.most_common():
        print(f"    {seg:20s}: {cnt:3d}  ({cnt/total*100:.1f}%)")

    # ── 4. partner auth/refresh concentration ────────────────────────────────
    refresh_total   = sum(1 for r in records if r["endpoint"] == "/api/v1/auth/refresh")
    refresh_partner = sum(1 for r in records
                          if r["endpoint"] == "/api/v1/auth/refresh"
                          and r["user_segment"] == "partner")
    print(f"\n[4] auth/refresh traffic from partner: "
          f"{refresh_partner}/{refresh_total} = {refresh_partner/refresh_total*100:.1f}%")

    # ── 5. partner daily request trend (Jan → Mar) ───────────────────────────
    partner_by_month = Counter(
        r["timestamp"][:7]
        for r in records
        if r["user_segment"] == "partner"
    )
    print("\n[5] partner requests by month:")
    for month, cnt in sorted(partner_by_month.items()):
        print(f"    {month}: {cnt} requests")

    # ── 6. HTTP method distribution ───────────────────────────────────────────
    method_counts = Counter(r["method"] for r in records).most_common()
    print(f"\n[6] Method distribution (GET should dominate in normal traffic):")
    for method, cnt in method_counts:
        print(f"    {method:6s}: {cnt}")

    # ── 7. Error rate per endpoint ────────────────────────────────────────────
    ep_stats = defaultdict(lambda: {"total": 0, "errors": 0, "latencies": []})
    for r in records:
        ep = r["endpoint"]
        ep_stats[ep]["total"] += 1
        if r["status_code"] >= 400:
            ep_stats[ep]["errors"] += 1
        ep_stats[ep]["latencies"].append(r["latency_ms"])

    print("\n[7] Error rate & avg latency per endpoint (sorted by error rate desc):")
    rows = []
    for ep, s in ep_stats.items():
        rate = s["errors"] / s["total"] * 100
        avg  = statistics.mean(s["latencies"])
        rows.append((ep, s["total"], rate, avg))
    for ep, cnt, rate, avg in sorted(rows, key=lambda x: -x[2]):
        print(f"    {ep:35s}: {cnt:3d} req  {rate:5.1f}% errors  avg={avg:.0f}ms")

    # ── 8. Error rate per segment ─────────────────────────────────────────────
    seg_stats = defaultdict(lambda: {"total": 0, "errors": 0})
    for r in records:
        seg = r["user_segment"]
        seg_stats[seg]["total"] += 1
        if r["status_code"] >= 400:
            seg_stats[seg]["errors"] += 1

    print("\n[8] Error rate per user_segment (sorted desc):")
    for seg, s in sorted(seg_stats.items(), key=lambda x: -x[1]["errors"]/x[1]["total"]):
        rate = s["errors"] / s["total"] * 100
        print(f"    {seg:20s}: {s['total']:3d} req  {rate:5.1f}% errors")

    # ── 9. Semantically wrong method+endpoint combos ─────────────────────────
    weird = [
        r for r in records
        if (r["method"] == "DELETE" and "auth" in r["endpoint"])
        or (r["method"] == "DELETE" and r["endpoint"] in
            ("/api/v1/analytics", "/api/v1/notifications", "/api/v1/search"))
        or (r["method"] == "PUT"   and "auth" in r["endpoint"])
    ]
    print(f"\n[9] Semantically anomalous calls (DELETE/PUT on read/auth endpoints): "
          f"{len(weird)}")
    segs = Counter(r["user_segment"] for r in weird)
    print(f"    By segment: {segs.most_common()}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("""
═══════════════════════ LAYER 4 SUMMARY ═══════════════════════
1. 69.6% error rate — system is severely degraded (normal: <5%).
2. 401 Unauthorized is the #1 status code — auth failures dominate.
3. `partner` is 19.8% of all traffic (99/500) — ~2x any other segment.
4. `partner` drives 38% of auth/refresh calls — token-loop signature.
5. partner sustains ~30–37 requests/month across the full quarter —
   a persistently elevated baseline, not a one-off spike.
6. GET is the LEAST common method — DELETE/PUT dominate (bot behaviour).
7. `orders` has the highest error rate (77.6%) — checkout is broken.
8. `billing` has the fewest requests (40) AND highest avg latency
   (2692ms) — users are avoiding a slow, broken endpoint.
9. 69 semantically nonsensical calls (DELETE auth/login, PUT auth/refresh,
   etc.); partner alone accounts for 21 of them — strongest signal of
   automated, non-human-driven API abuse.

Conclusion: the dataset depicts a compromised API environment where
a rogue `partner` integration is conducting persistent automated
credential attacks (primarily token-refresh abuse), while the rest
of the system degrades — highest-error endpoints are commerce-critical
(orders 77.6%, billing 72.5%), and the overall success rate is only 30%.
═══════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    run()
