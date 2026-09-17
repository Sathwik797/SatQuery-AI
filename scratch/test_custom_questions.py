import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_landing_and_arbitrary_questions():
    print("[1] Verifying landing page real manual input HTML...")
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
    
    assert 'id="landingQueryInput"' in html
    assert 'id="btnLandingSend"' in html
    assert 'id="queryInput"' in html
    assert 'id="btnSend"' in html
    assert 'class="composer-area"' in html
    print("  -> Both landingQueryInput and workspace queryInput are present in DOM.")

    print("\n[2] Testing acceptance test flow: Kolkata Demo + Arbitrary Custom Question...")
    # Load demo
    data = json.dumps({"sample_key": "kolkata"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/load_demo", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    prim_id = res["primary"]["id"]
    conv_id = "test-custom-conv-99"
    print(f"  -> Loaded Kolkata Scene (ID: {prim_id})")

    # Question 1: Arbitrary custom question from prompt
    custom_q1 = "What percentage of this image appears to be built-up?"
    print(f"  -> Submitting Custom Q1: '{custom_q1}'")
    p1 = json.dumps({"primary_id": prim_id, "secondary_id": None, "query": custom_q1, "conversation_id": conv_id}).encode("utf-8")
    req1 = urllib.request.Request(f"{BASE_URL}/api/analyze", data=p1, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req1) as resp:
        ans1 = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Response Q1: {ans1['answer'][:90]}... (Confidence: {ans1['confidence']})")
    assert ans1["answer"], "Custom question 1 returned empty answer"

    # Question 2: Follow-up question in the same conversation
    custom_q2 = "Where is the water?"
    print(f"  -> Submitting Follow-up Q2: '{custom_q2}'")
    p2 = json.dumps({"primary_id": prim_id, "secondary_id": None, "query": custom_q2, "conversation_id": conv_id}).encode("utf-8")
    req2 = urllib.request.Request(f"{BASE_URL}/api/analyze", data=p2, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req2) as resp:
        ans2 = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Response Q2: {ans2['answer'][:90]}... (Overlay: {ans2.get('overlay_url')})")
    assert ans2["overlay_url"], "Q2 should return evidence overlay"

    # Question 3: Second follow-up question
    custom_q3 = "What about vegetation?"
    print(f"  -> Submitting Follow-up Q3: '{custom_q3}'")
    p3 = json.dumps({"primary_id": prim_id, "secondary_id": None, "query": custom_q3, "conversation_id": conv_id}).encode("utf-8")
    req3 = urllib.request.Request(f"{BASE_URL}/api/analyze", data=p3, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req3) as resp:
        ans3 = json.loads(resp.read().decode("utf-8"))
    print(f"  -> Response Q3: {ans3['answer'][:90]}...")
    assert ans3["answer"], "Q3 should return conversational answer"

    print("\nALL CUSTOM ARBITRARY QUESTION TESTS PASSED!")

if __name__ == "__main__":
    test_landing_and_arbitrary_questions()
