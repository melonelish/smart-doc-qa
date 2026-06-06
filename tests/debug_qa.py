"""Quick QA test — run after test_table_qa.py"""
import json, urllib.request, urllib.error

KB_ID = "fa0febfe-d089-4756-a669-e96145b91024"  # <-- paste the KB ID from the last run

body = json.dumps({"kb_id": KB_ID, "question": "Q3的利润率是多少？"}).encode()
req = urllib.request.Request(
    "http://localhost:8000/api/v1/qa/ask",
    data=body,
    headers={"Content-Type": "application/json"},
)
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"Answer: {data['answer'][:500]}")
    print(f"Method: {data['retrieval_method']}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:500]}")
except Exception as e:
    print(f"Error: {e}")