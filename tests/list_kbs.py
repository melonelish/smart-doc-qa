import json, urllib.request

# List enterprise KBs
req = urllib.request.Request("http://localhost:8000/api/v1/knowledge-bases/?domain=enterprise")
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
kbs = data.get("knowledge_bases", []) or data
if isinstance(kbs, list) and kbs:
    print(kbs[0]["id"])
else:
    print("NONE")