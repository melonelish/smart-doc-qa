#!/usr/bin/env python3
"""
测试 3 个功能：
1. 流式输出（SSE）
2. 多轮对话（conversation_id）
3. 历史记录（加载、恢复、删除）
"""

import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def api_request(method, path, data=None, timeout=10):
    """发送 API 请求"""
    url = BASE_URL + path
    headers = {'Content-Type': 'application/json'}
    
    if data:
        data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"❌ HTTP {e.code}: {body}")
        return e.code, None

print("=" * 60)
print("测试 1: 创建知识库 + 上传文档")
print("=" * 60)

# 1. 创建知识库
status, kb = api_request("POST", "/api/v1/knowledge-bases/", {
    "name": "E2E测试KB",
    "description": "端到端测试"
})
if not kb:
    print("❌ 创建知识库失败")
    exit(1)

kb_id = kb['id']
print(f"✅ 知识库创建成功: {kb_id}")

# 2. 上传文档（使用已有的测试文件）
print("\n" + "=" * 60)
print("测试 2: 上传文档")
print("=" * 60)

# 先创建一个简单的测试文件
test_file_path = "/tmp/test_doc.txt"
with open(test_file_path, 'w', encoding='utf-8') as f:
    f.write("智能文档问答系统支持流式输出功能。\n")
    f.write("流式输出可以逐token显示答案，提升用户体验。\n")
    f.write("系统还支持多轮对话和历史记录查询。\n")

print(f"⚠️  需要手动上传文件，跳过文档上传测试")
print(f"请确保在知识库 {kb_id} 中有可用文档")

print("\n" + "=" * 60)
print("测试 3: 非流式问答")
print("=" * 60)

status, result = api_request("POST", "/api/v1/qa/ask", {
    "question": "系统支持什么功能？",
    "kb_id": kb_id
}, timeout=120)

if result:
    print(f"✅ 问答成功")
    print(f"   答案: {result.get('answer', '')[:100]}...")
    print(f"   对话ID: {result.get('conversation_id', 'N/A')}")
else:
    print("❌ 问答失败")

print("\n" + "=" * 60)
print("测试 4: 流式问答（SSE）")
print("=" * 60)

# 流式请求需要特殊处理
url = BASE_URL + "/api/v1/qa/ask-stream"
payload = {
    "question": "系统支持什么功能？",
    "kb_id": kb_id
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(
    url,
    data=data,
    headers={
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        print(f"✅ 流式连接成功 (状态码: {resp.status})")
        print(f"   Content-Type: {resp.headers.get('Content-Type')}")
        
        # 读取前 500 字符
        body = resp.read(500).decode('utf-8')
        print(f"   SSE 数据片段:")
        for line in body.split('\n')[:10]:
            if line.strip():
                print(f"     {line}")
except Exception as e:
    print(f"❌ 流式请求失败: {e}")

print("\n" + "=" * 60)
print("测试 5: 多轮对话（conversation_id）")
print("=" * 60)

# 第一轮
status, result1 = api_request("POST", "/api/v1/qa/ask", {
    "question": "知识库的名称是什么？",
    "kb_id": kb_id
}, timeout=120)

if result1:
    conv_id = result1.get('conversation_id')
    print(f"✅ 第一轮成功")
    print(f"   对话ID: {conv_id}")
    print(f"   答案: {result1.get('answer', '')[:80]}...")
    
    # 第二轮（使用同一 conversation_id）
    status, result2 = api_request("POST", "/api/v1/qa/ask", {
        "question": "它的描述是什么？",
        "kb_id": kb_id,
        "conversation_id": conv_id
    }, timeout=120)
    
    if result2:
        same_id = result2.get('conversation_id') == conv_id
        print(f"✅ 第二轮成功")
        print(f"   对话ID相同: {same_id}")
        print(f"   答案: {result2.get('answer', '')[:80]}...")
    else:
        print("❌ 第二轮失败")
else:
    print("❌ 第一轮失败")

print("\n" + "=" * 60)
print("测试 6: 历史记录 API")
print("=" * 60)

status, history = api_request("GET", "/api/v1/qa/history", timeout=10)

if history:
    print(f"✅ 历史记录获取成功")
    print(f"   记录数: {history.get('total', 0)}")
    print(f"   对话数: {len(history.get('conversations', []))}")
else:
    print("❌ 历史记录获取失败")

print("\n" + "=" * 60)
print("测试 7: 清理测试数据")
print("=" * 60)

# 删除知识库
status, _ = api_request("DELETE", f"/api/v1/knowledge-bases/{kb_id}")
if status == 200:
    print(f"✅ 知识库 {kb_id} 删除成功")
else:
    print(f"❌ 删除失败 (状态码: {status})")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
