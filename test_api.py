"""Quick API test — run after starting backend."""
import sys, json, requests

BASE = "http://localhost:8000/api/v1"

def test(name, method, path, body=None, expected=200):
    url = BASE + path
    print(f"  ▶ {name} ... ", end="", flush=True)
    try:
        if method == "GET":
            r = requests.get(url, headers=h, timeout=30)
        else:
            r = requests.post(url, headers=h, json=body, timeout=30)
        ok = (r.status_code == expected)
        marker = "✅" if ok else f"❌ ({r.status_code})"
        print(f"{marker} {r.json() if not ok else ''}")
        if not ok:
            print(f"     {r.text[:200]}")
        return ok
    except Exception as e:
        print(f"💥 {e}")
        return False

# Auth
h = {}
print("\n═══ Login ═══")
r = requests.post(BASE + "/auth/login", json={"username": "admin", "password": "admin123"})
print(f"  Login: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    tok = data.get("access_token", "")
    h["Authorization"] = f"Bearer {tok}"
    print(f"  Token: {tok[:30]}...")

    # Test meta detection
    print("\n═══ Meta Question ═══")
    test("你是什么模型", "POST", "/qa/ask", {
        "question": "你是什么模型",
        "kb_id": "b2e4c78a-4663-4a0c-95e2-0970f06d6a8a"
    })

    # Test health
    print("\n═══ Health ═══")
    test("health", "GET", "/../health")

    # Test KB list
    print("\n═══ Knowledge Bases ═══")
    test("list KBs", "GET", "/knowledge-bases/")

    print("\n═══ Settings ═══")
    test("model configs", "GET", "/model-configs/")

    print("\n═══ Model Config Test ═══")
    test("test connection", "POST", "/model-configs/test-connection", {
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "api_key": "sk-test123",
        "model_name": "deepseek-chat"
    }, expected=200)

print("\n✅ All done")
