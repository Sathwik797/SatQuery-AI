import urllib.request
import urllib.parse
import json
import io
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_html_served():
    print("[1] Testing GET / (Frontend serving)...")
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        html = resp.read().decode("utf-8")
        
    # Check for core design and UI elements
    required_strings = [
        "SatQuery AI",
        "Ask questions about satellite imagery using natural language",
        "Upload satellite imagery and ask anything",
        "Single Image",
        "Compare Two Images (T1 / T2)",
        "Optical + SAR Dual Sensor",
        "Try a demo ▾",
        "🌆 Kolkata Urban",
        "🔥 California Wildfire",
        "🛰️ Cartosat-2S + RISAT-1A",
        "How was this determined?",
        "downloadExecutiveReport",
        "downloadJsonReport",
        "--emerald: #059669;",
        "--bg: #F8FAFC;",
        "--text: #0F172A;"
    ]
    for s in required_strings:
        assert s in html, f"Missing required string in HTML: '{s}'"
    print("  -> HTML verification PASSED (All redesign elements, palette, and components present).")

def test_single_image_captioning_and_grounding():
    print("[2] Testing Demo Load & Analysis (Kolkata)...")
    # 1. Load Demo
    data = json.dumps({"sample_key": "kolkata"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/load_demo", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    primary_id = res["primary"]["id"]
    print(f"  -> Loaded Kolkata demo (ID: {primary_id})")

    # 2. Query 1: Captioning
    payload = json.dumps({
        "primary_id": primary_id,
        "secondary_id": None,
        "query": "Describe this scene.",
        "conversation_id": "test-conv-1"
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/analyze", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        ans1 = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Captioning Answer: {ans1['answer'][:80]}... (Confidence: {ans1['confidence']})")
    assert ans1["answer"], "Captioning returned empty answer"
    assert ans1["task"] == "captioning"

    # 3. Query 2: Grounding
    payload2 = json.dumps({
        "primary_id": primary_id,
        "secondary_id": None,
        "query": "Where is the water?",
        "conversation_id": "test-conv-1"
    }).encode("utf-8")
    req2 = urllib.request.Request(f"{BASE_URL}/api/analyze", data=payload2, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req2) as resp:
        ans2 = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Grounding Answer: {ans2['answer'][:80]}... (Overlay: {ans2.get('overlay_url')})")
    assert ans2["overlay_url"], "Grounding should return an overlay URL"
    assert ans2["bounding_box"], "Grounding should return a bounding box"

    # Verify overlay URL is reachable
    overlay_req = urllib.request.Request(f"{BASE_URL}{ans2['overlay_url']}")
    with urllib.request.urlopen(overlay_req) as resp:
        assert resp.status == 200, f"Overlay image {ans2['overlay_url']} not reachable"
    print("  -> Overlay asset HTTP 200 verified.")

def test_bitemporal_change():
    print("[3] Testing Bi-temporal Change Detection Demo...")
    data = json.dumps({"sample_key": "bitemporal"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/load_demo", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    p_id = res["primary"]["id"]
    s_id = res["secondary"]["id"]
    print(f"  -> Loaded Bi-temporal (T1: {p_id}, T2: {s_id})")

    payload = json.dumps({
        "primary_id": p_id,
        "secondary_id": s_id,
        "query": "Has construction increased between these two images?",
        "conversation_id": "test-conv-2"
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/analyze", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        ans = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Change Detection Answer: {ans['answer']}")
    print(f"  -> Task: {ans['task']}, Tool: {ans['tool']}, Area: {ans['evidence'].get('burn_area_hectares')} ha")
    assert ans["overlay_url"] is not None, "Change detection should return overlay mask"
    print("  -> Bi-temporal change workflow PASSED.")

def test_optical_sar():
    print("[4] Testing Optical + SAR Cross-Modal Fusion...")
    data = json.dumps({"sample_key": "optical_sar"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/load_demo", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    p_id = res["primary"]["id"]
    s_id = res["secondary"]["id"]
    print(f"  -> Loaded Optical-SAR (Optical: {p_id}, SAR: {s_id})")

    payload = json.dumps({
        "primary_id": p_id,
        "secondary_id": s_id,
        "query": "What can these two images tell us about this area?",
        "conversation_id": "test-conv-3"
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/analyze", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        ans = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Optical-SAR Answer: {ans['answer'][:90]}...")
    print(f"  -> Task: {ans['task']}, Confidence: {ans['confidence']}")
    assert ans["overlay_url"] is not None, "Optical-SAR should return overlay"
    print("  -> Optical + SAR workflow PASSED.")

if __name__ == "__main__":
    try:
        test_html_served()
        test_single_image_captioning_and_grounding()
        test_bitemporal_change()
        test_optical_sar()
        print("\nALL WORKFLOW TESTS COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
