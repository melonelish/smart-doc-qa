"""Verify the /file endpoint returns PDF content correctly."""
import urllib.request, json

# List documents from the KB we just created
kb_id = "3b9b6051-3ce0-4d43-b4b1-38561da09f8e"
url = f"http://localhost:8000/api/v1/knowledge-bases/{kb_id}/documents"
resp = urllib.request.urlopen(url)
data = json.loads(resp.read())
items = data.get("items", [])
print(f"Found {len(items)} documents")
for d in items:
    doc_id = d["id"]
    print(f"doc_id={doc_id} filename={d['filename']} file_type={d['file_type']}")
    # Test the /file endpoint
    file_resp = urllib.request.urlopen(f"http://localhost:8000/api/v1/documents/{doc_id}/file")
    ct = file_resp.headers.get("Content-Type")
    body = file_resp.read()
    print(f"  /file status={file_resp.status} content-type={ct}")
    print(f"  size={len(body)} bytes")
    print(f"  starts_with_%PDF={body[:4] == b'%PDF'}")
    if body[:4] == b"%PDF":
        print("  >>> PDF preview endpoint works correctly! <<<")