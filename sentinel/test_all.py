"""SENTINEL end-to-end test script."""
import httpx
import json

BASE = "http://localhost:8000"

def test(name, fn):
    try:
        result = fn()
        print(f"[PASS] {name}")
        return result
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return None

# 1. Health
test("Backend health", lambda: httpx.get(f"{BASE}/health", timeout=5).json())

# 2. SCAMWatch English
print("\n--- SCAMWatch English ---")
r = test("SCAMWatch analyze (EN)", lambda: httpx.post(f"{BASE}/api/scamwatch/analyze", json={
    "text": "URGENT: Your SBI account KYC is expired. Click here to update: http://sbi-kyc-update.xyz",
    "channel": "sms",
    "language": "en"
}, timeout=60).json())
if r:
    print(f"  Risk: {r['risk_level']} ({r['risk_score']:.2f})")
    print(f"  Type: {r.get('scam_type')}")
    print(f"  Verdict: {r['verdict'][:60]}")
    print(f"  Indicators: {len(r['indicators'])}")

# 3. SCAMWatch Hindi
print("\n--- SCAMWatch Hindi ---")
r2 = test("SCAMWatch analyze (HI)", lambda: httpx.post(f"{BASE}/api/scamwatch/analyze", json={
    "text": "Sir, I am calling from CBI. You are under digital arrest. Transfer Rs 5 lakh immediately.",
    "channel": "call",
    "language": "hi"
}, timeout=60).json())
if r2:
    print(f"  Risk: {r2['risk_level']} ({r2['risk_score']:.2f})")
    print(f"  Translated: {r2.get('translated_verdict', 'N/A')[:60]}")
    print(f"  Language: {r2.get('target_language')}")

# 4. Citizen Alert
if r:
    print("\n--- Citizen Alert ---")
    alert = test("Citizen alert", lambda: httpx.post(f"{BASE}/api/scamwatch/alert/{r['analysis_id']}", timeout=15).json())
    if alert:
        print(f"  Verdict: {alert['one_line_verdict'][:50]}")
        print(f"  Actions: {len(alert['recommended_actions'])}")
        print(f"  Contacts: {len(alert['emergency_contacts'])}")

# 5. Evidence Kit
print("\n--- FRAUDGraph Evidence Kit ---")
fraud = test("FRAUDGraph analyze", lambda: httpx.post(f"{BASE}/api/fraudgraph/analyze", json={
    "phones": ["9876543210", "8765432109"],
    "accounts": ["HDFC0000123456"],
    "victim_statement": "I was called by 9876543210 posing as CBI. They transferred money to HDFC0000123456."
}, timeout=120).json())
if fraud:
    sid = fraud["session_id"]
    print(f"  Session: {sid[:8]}")
    print(f"  Risk: {fraud['risk_level']} ({fraud['risk_score']:.2f})")
    print(f"  Entities: {len(fraud['entities'])}")
    kit = test("Evidence kit ZIP", lambda: httpx.get(f"{BASE}/api/fraudgraph/evidence-kit/{sid}", timeout=15))
    if kit:
        print(f"  ZIP size: {len(kit.content)} bytes")

# 6. GeoIntel
print("\n--- GeoIntel ---")
incidents = test("Geo incidents", lambda: httpx.get(f"{BASE}/api/geo/incidents?limit=10", timeout=10).json())
if incidents:
    print(f"  Incidents: {len(incidents)}")

heatmap = test("Geo heatmap", lambda: httpx.get(f"{BASE}/api/geo/heatmap", timeout=10).json())
if heatmap:
    print(f"  Hotspots: {len(heatmap)}")

# 7. Intelligence Dashboard
print("\n--- Intelligence Dashboard ---")
stats = test("Intelligence stats", lambda: httpx.get(f"{BASE}/api/intelligence/stats", timeout=10).json())
if stats:
    print(f"  Total events: {stats['total_events']}")

print("\n=== ALL TESTS COMPLETE ===")
