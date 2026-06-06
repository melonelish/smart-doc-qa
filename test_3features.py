#!/usr/bin/env python3
"""
快速测试 3 个功能（后端 API）
1. 流式输出（SSE）
2. 多轮对话（conversation_id）
3. 历史记录（加载、恢复、删除）
"""

import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000"

def post(path, data):
    """POST 请求"""
    url = BASE + path
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, 
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()[:200]}")
        return e.code, None

def get(path):
    """GET 请求"""
    url = BASE + path
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        print(f"❌ {e}")
        return None, None

print("=" * 70)
print("测试 1: 非流式问答 + 多轮对话")
print("=" * 70)

# 使用一个已有的知识库（合同文档对比测试，有 7 个文档）
KB_ID = "b2e4c78a-4663-4a0c-95e2-0970f06d6a8a"

# 第一轮
status, r1 = post("/api/v1/qa/ask", {
    "question": "知识库的名称是什么？",
    "kb_id": KB_ID
})

if r1:
    conv_id = r1.get("conversation_id")
    print(f"✅ 第一轮成功")
    print(f"   对话 ID: {conv_id}")
    print(f"   答案: {r1.get('answer', '')[:80]}...")
    
    # 第二轮（多轮）
    time.sleep(1)
    status2, r2 = post("/api/v1/qa/ask", {
        "question": "它的描述是什么？",
        "kb_id": KB_ID,
        "conversation_id": conv_id
    })
    
    if r2:
        same = r2.get("conversation_id") == conv_id
        print(f"✅ 第二轮成功")
        print(f"   对话 ID 相同: {same}")
        print(f"   答案: {r2.get('answer', '')[:80]}...")
    else:
        print("❌ 第二轮失败")
else:
    print("❌ 第一轮失败")

print()
print("=" * 70)
print("测试 2: 流式问答（SSE）")
print("=" * 70)

# 流式请求
url = BASE + "/api/v1/qa/ask-stream"
data = json.dumps({
    "question": "知识库有多少个文档？",
    "kb_id": KB_ID
}).encode()

req = urllib.request.Request(url, data=data,
    headers={
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }, method="POST")

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        print(f"✅ 流式连接成功 (状态码: {resp.status})")
        print(f"   Content-Type: {resp.headers.get('Content-Type')}")
        print(f"   SSE 数据片段:")
        
        # 读取前 500 字节
        chunk = resp.read(500).decode()
        for line in chunk.split("\n")[:10]:
            if line.strip():
                print(f"     {line[:100]}")
except Exception as e:
    print(f"❌ 流式请求失败: {e}")

print()
print("=" * 70)
print("测试 3: 历史记录 API")
print("=" * 70)

status, history = get("/api/v1/qa/history")

if history:
    total = history.get("total", 0)
    convs = history.get("conversations", [])
    print(f"✅ 历史记录获取成功")
    print(f"   总记录数: {total}")
    print(f"   对话数: {len(convs)}")
    
    if convs:
        print(f"   最新对话: {convs[0].get('conversation_id', '')[:20]}...")
else:
    print("❌ 历史记录获取失败")

print()
print("=" * 70)
print("测试完成！")
print("=" * 70)
print()
print("📱 前端 UI 测试（请在浏览器中验证）:")
print("1. 打开 http://127.0.0.1:5173/")
print("2. 测试流式输出：发送消息，观察是否逐 token 显示")
print("3. 测试多轮对话：连续发送 2 条消息，检查是否上下文连贯")
print("4. 测试历史记录：点击「📜 历史」按钮，检查是否正常加载、恢复、删除")
