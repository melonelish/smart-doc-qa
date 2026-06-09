"""Final integrated API test."""
import sys, json, time, requests

BASE = "http://localhost:8000"
passed = failed = 0

def ok(cond, msg):
    global passed, failed
    if cond:
        passed += 1; print(f"  ✅ {msg}")
    else:
        failed += 1; print(f"  ❌ {msg}")

# 1. Health
r = requests.get(f"{BASE}/health", timeout=10)
ok(r.status_code == 200 and r.json()["status"] == "healthy", f"Health check ({r.status_code})")

# 2. Login
r = requests.post(f"{BASE}/api/v1/auth/login", json={"username":"admin","password":"admin123"}, timeout=10)
ok(r.status_code == 200, f"Login ({r.status_code})")
tok = r.json().get("access_token","") if r.status_code == 200 else ""

# 3. Meta Question (no auth needed actually, but include token)
if tok:
    r = requests.post(f"{BASE}/api/v1/qa/ask",
        headers={"Authorization": f"Bearer {tok}"},
        json={"question": "你是什么模型", "kb_id": "b2e4c78a-4663-4a0c-95e2-0970f06d6a8a"},
        timeout=30)
    body = r.json()
    is_meta = "deepseek" in str(body).lower() or "meta" in str(body).lower()
    ok(r.status_code in (200, 404) and is_meta, f"Meta question ({r.status_code}): {str(body)[:80]}")
else:
    ok(False, "Login failed — can't test QA")

# 4. Model configs list
r = requests.get(f"{BASE}/api/v1/model-configs/", headers={"Authorization":f"Bearer {tok}"}, timeout=10)
ok(r.status_code == 200, f"Model configs ({r.status_code})")

# 5. Knowledge bases
r = requests.get(f"{BASE}/api/v1/knowledge-bases/", timeout=10)
ok(r.status_code == 200, f"KB list ({r.status_code})")

print(f"\n═══ Results: {passed} passed, {failed} failed ═══")
