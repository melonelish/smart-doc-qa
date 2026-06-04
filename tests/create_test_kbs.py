"""
自动创建测试知识库和文档，用于验证跨文档对比分析功能。

用法:
    python tests/create_test_kbs.py

依赖: pip install requests
"""

import json
import os
import sys
import time
import requests

BASE_URL = "http://localhost:8000/api/v1"
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


def api(method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    kwargs.setdefault("timeout", 120)
    resp = method(url, **kwargs)
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    if resp.status_code >= 400:
        print(f"  [ERROR] {resp.status_code}: {data}")
        return None
    return data


def create_kb(name, domain="enterprise"):
    print(f"\n=== 创建知识库: {name} ===")
    data = api(requests.post, "/knowledge-bases/",
               json={"name": name, "description": f"用于测试的{name}", "domain": domain})
    if data:
        print(f"  KB ID: {data['id']}")
    return data


def upload_doc(filepath):
    filename = os.path.basename(filepath)
    print(f"\n--- 上传文档: {filename} ---")
    with open(filepath, "rb") as f:
        files = {"file": (filename, f, "text/markdown")}
        data = api(requests.post, "/documents/upload", files=files)
    if data:
        print(f"  Doc ID: {data['id']}, Status: {data['status']}")
    return data


def process_doc(doc_id):
    print(f"  处理文档 {doc_id}...")
    data = api(requests.post, f"/documents/{doc_id}/process")
    if data:
        print(f"  Status: {data.get('status', data)}")
    return data


def add_to_kb(kb_id, doc_ids):
    print(f"  添加到知识库...")
    data = api(requests.post, f"/knowledge-bases/{kb_id}/documents",
               json={"doc_ids": doc_ids})
    if data:
        print(f"  Result: {data}")
    return data


def rebuild_index(kb_id):
    print(f"  重建知识库索引...")
    data = api(requests.post, f"/knowledge-bases/{kb_id}/rebuild-index")
    if data:
        print(f"  Result: {data}")
    return data


def main():
    # 1. 创建知识库：季度报表对比
    kb1 = create_kb("季度报表对比测试")
    if not kb1:
        print("创建知识库失败，退出")
        sys.exit(1)
    kb1_id = kb1["id"]

    # 2. 上传并处理 Q1/Q2/Q3 季度报表
    doc_ids1 = []
    for fname in ["Q1_季度财报.md", "Q2_季度财报.md", "Q3_季度财报.md"]:
        fpath = os.path.join(TEST_DATA_DIR, fname)
        doc = upload_doc(fpath)
        if doc:
            doc_ids1.append(doc["id"])
            process_doc(doc["id"])

    # 3. 将文档关联到知识库并重建索引
    if doc_ids1:
        add_to_kb(kb1_id, doc_ids1)
        rebuild_index(kb1_id)

    # 4. 创建知识库：合同条款对比测试
    kb2 = create_kb("合同条款对比测试")
    if not kb2:
        print("创建知识库失败，退出")
        sys.exit(1)
    kb2_id = kb2["id"]

    # 5. 上传并处理合同文档
    doc_ids2 = []
    for fname in ["合同A_设备采购协议.md", "合同B_软件许可协议.md"]:
        fpath = os.path.join(TEST_DATA_DIR, fname)
        doc = upload_doc(fpath)
        if doc:
            doc_ids2.append(doc["id"])
            process_doc(doc["id"])

    # 6. 将合同文档关联到知识库并重建索引
    if doc_ids2:
        add_to_kb(kb2_id, doc_ids2)
        rebuild_index(kb2_id)

    print("\n" + "=" * 60)
    print("所有操作完成！")
    print(f"知识库1: 季度报表对比测试 (ID: {kb1_id})")
    print(f"  文档: Q1_季度财报, Q2_季度财报, Q3_季度财报")
    print(f"知识库2: 合同条款对比测试 (ID: {kb2_id})")
    print(f"  文档: 合同A_设备采购协议, 合同B_软件许可协议")
    print("=" * 60)


if __name__ == "__main__":
    main()