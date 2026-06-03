"""Test: upload PDF with tables + ask numeric question (with debug)."""
import json, os, urllib.request, urllib.error, uuid, pathlib

BASE = "http://localhost:8000"
KB_NAME = f"Test KB {uuid.uuid4().hex[:6]}"
PDF_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "test_docs", "quarterly_report_2026.pdf"))

# ── 1) Create enterprise KB ──
req = urllib.request.Request(
    f"{BASE}/api/v1/knowledge-bases/",
    data=json.dumps({"name": KB_NAME, "domain": "enterprise"}).encode(),
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
kb = json.loads(resp.read())
kb_id = kb["id"]
print(f"[OK] Created KB: {kb_id}")

# ── 2) Upload PDF ──
with open(PDF_PATH, "rb") as f:
    pdf_data = f.read()
boundary = "----" + uuid.uuid4().hex
req = urllib.request.Request(
    f"{BASE}/api/v1/knowledge-bases/{kb_id}/upload",
    data=(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="quarterly_report_2026.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n".encode()
        + pdf_data +
        f"\r\n--{boundary}--\r\n".encode()
    ),
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
resp = urllib.request.urlopen(req)
upload = json.loads(resp.read())
print(f"[OK] Uploaded: {upload['filename']}")

# ── 3) Verify disk ──
store_dir = pathlib.Path(os.path.dirname(__file__)).parent / "data" / "vector_store" / f"kb_{kb_id}"
print(f"[OK] FAISS: {(store_dir / 'index.faiss').exists()}")
for p in sorted(store_dir.iterdir()):
    print(f"    {p.name} ({p.stat().st_size} bytes)")

# ── 4) Ask numeric question ──
body = json.dumps({"kb_id": kb_id, "question": "Q3的利润率是多少？相比Q2有什么变化？"}).encode()
req = urllib.request.Request(
    f"{BASE}/api/v1/qa/ask", data=body,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    qa = json.loads(resp.read())
    print(f"\n[OK] Answer:\n{qa['answer'][:600]}")
    print(f"[OK] Method: {qa['retrieval_method']}")
except urllib.error.HTTPError as e:
    print(f"\n[FAIL] HTTP {e.code}:")
    print(e.read().decode()[:500])

print("\n*** DONE ***")