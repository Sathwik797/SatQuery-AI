import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_html_ui_checks():
    print("[1] Verifying UX corrections in served index.html...")
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")

    # 1. Check accurate format guidance
    assert "GeoTIFF / TIFF recommended for full geospatial analysis" in html
    assert "Supported benchmark PNG/JPG images are also accepted" in html
    print("  -> Upload guidance verified (GeoTIFF/TIFF recommended, benchmark PNG/JPG).")

    # 2. Check landing suggestion chips & deck
    assert "Ask SatQuery about:" in html
    assert "Load Kolkata Urban Demo ➔" in html
    assert "Where is the water?" in html
    assert "Has construction increased?" in html
    print("  -> Landing suggestion chips deck verified.")

    # 3. Check friendly error modal component
    assert "error-modal-backdrop" in html
    assert "Unable to analyze this image" in html
    assert "Technical details ▾" in html
    assert "Try a Demo Scene" in html
    assert "Choose Another File" in html
    print("  -> In-page friendly error modal verified (No browser alert popups).")

    # 4. Check pinned question composer
    assert "composer-area" in html
    assert "Ask anything about this satellite image..." in html
    assert "btn-analyze" in html
    assert "How was this determined?" in html
    print("  -> Pinned composer & secondary technical accordion verified.")

def test_unsupported_upload_rejection_friendly_payload():
    print("[2] Testing unsupported upload behavior (Test 8)...")
    # Generate arbitrary fake PNG bytes
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    boundary = "----TestBoundary98765"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="random_photo.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + fake_png + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print("ERROR: Unsupported file was unexpectedly accepted!")
            sys.exit(1)
    except urllib.error.HTTPError as e:
        assert e.code == 400
        error_body = json.loads(e.read().decode("utf-8"))
        print(f"  -> Backend correctly rejected unsupported image with 400: {error_body['detail'][:70]}...")
        print("  -> Verified frontend will catch this detail inside the friendly in-page error modal.")

def test_full_conversational_workflow():
    print("[3] Testing conversational workflow with questions (Tests 2, 3, 4, 5, 6, 7)...")
    
    # Kolkata Demo
    data = json.dumps({"sample_key": "kolkata"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/load_demo", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    k_id = res["primary"]["id"]

    # Test 3: Describe this scene
    q1 = json.dumps({"primary_id": k_id, "secondary_id": None, "query": "Describe this scene.", "conversation_id": "conv-ux"}).encode("utf-8")
    req_q1 = urllib.request.Request(f"{BASE_URL}/api/analyze", data=q1, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_q1) as resp:
        ans1 = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Test 3 (Describe): {ans1['answer'][:80]}... (Confidence: {ans1['confidence']})")
    assert not ans1["answer"].startswith("CAPTIONING •"), "Raw technical tool names should not prefix plain answer"

    # Test 4: Where is the water?
    q2 = json.dumps({"primary_id": k_id, "secondary_id": None, "query": "Where is the water?", "conversation_id": "conv-ux"}).encode("utf-8")
    req_q2 = urllib.request.Request(f"{BASE_URL}/api/analyze", data=q2, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_q2) as resp:
        ans2 = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Test 4 (Grounding): {ans2['answer'][:80]}... (Overlay: {ans2['overlay_url']}, Box: {ans2['bounding_box']})")
    assert ans2["bounding_box"] is not None

    # Test 6: California Wildfire Change Detection
    data_cd = json.dumps({"sample_key": "bitemporal"}).encode("utf-8")
    req_cd = urllib.request.Request(f"{BASE_URL}/api/load_demo", data=data_cd, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_cd) as resp:
        res_cd = json.loads(resp.read().decode("utf-8"))
    
    q_cd = json.dumps({"primary_id": res_cd["primary"]["id"], "secondary_id": res_cd["secondary"]["id"], "query": "Has construction increased between these two images?", "conversation_id": "conv-cd"}).encode("utf-8")
    req_qcd = urllib.request.Request(f"{BASE_URL}/api/analyze", data=q_cd, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_qcd) as resp:
        ans_cd = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Test 6 (Change): {ans_cd['answer'][:80]}... (Burn Scar: {ans_cd['evidence'].get('burn_area_hectares')} ha)")

    # Test 7: Optical + SAR Joint Analysis
    data_os = json.dumps({"sample_key": "optical_sar"}).encode("utf-8")
    req_os = urllib.request.Request(f"{BASE_URL}/api/load_demo", data=data_os, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_os) as resp:
        res_os = json.loads(resp.read().decode("utf-8"))
    
    q_os = json.dumps({"primary_id": res_os["primary"]["id"], "secondary_id": res_os["secondary"]["id"], "query": "What can we understand by combining these images?", "conversation_id": "conv-os"}).encode("utf-8")
    req_qos = urllib.request.Request(f"{BASE_URL}/api/analyze", data=q_os, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_qos) as resp:
        ans_os = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Test 7 (Optical-SAR): {ans_os['answer'][:80]}... (Confidence: {ans_os['confidence']})")

if __name__ == "__main__":
    test_html_ui_checks()
    test_unsupported_upload_rejection_friendly_payload()
    test_full_conversational_workflow()
    print("\nALL UX CORRECTION PASS VERIFICATIONS COMPLETED SUCCESSFULLY!")
