import subprocess
import time
import urllib.request
import json
import sys
import os

BASE = "http://127.0.0.1:8000"
FRONTEND = "http://127.0.0.1:5173"
PYTHON = "D:/Anaconda/python.exe"
PROJECT_DIR = "D:/XM/smart-doc-qa"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def http_get(url, timeout=5):
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        return r.status, r.read().decode()
    except Exception as e:
        return None, str(e)

def http_post(url, data, timeout=60):
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)

def main():
    results = []
    
    # 1. 启动后端
    log("=== 启动后端 ===")
    backend = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    log(f"后端已启动 PID={backend.pid}")
    
    # 2. 等待后端就绪
    log("等待后端启动...")
    for i in range(30):
        time.sleep(2)
        status, body = http_get(f"{BASE}/health")
        if status == 200:
            log("✅ 后端已就绪")
            break
        log(f"  等待中... ({i+1}/30)")
    else:
        log("❌ 后端启动超时")
        backend.kill()
        return
    
    # 3. 跑测试
    log("\n=== 开始测试 ===")
    
    # T1: 健康检查
    status, body = http_get(f"{BASE}/health")
    results.append(("T1", "健康检查", "✅ 通过" if status == 200 else "❌ 失败", body[:100]))
    
    # T2: 知识库列表
    status, body = http_get(f"{BASE}/api/v1/knowledge-bases/")
    results.append(("T2", "知识库列表", "✅ 通过" if status == 200 else "❌ 失败", body[:100]))
    
    if status == 200:
        kbs = json.loads(body)["items"]
        kb_id = kbs[0]["id"] if kbs else None
        
        # T3: 问答功能
        if kb_id:
            log("测试问答功能（可能需要 20 秒）...")
            status, body = http_post(
                f"{BASE}/api/v1/qa/ask",
                {"kb_id": kb_id, "question": "简单介绍", "use_rerank": False},
                timeout=60
            )
            if status == 200:
                data = json.loads(body)
                results.append(("T3", "问答功能", "✅ 通过", data["answer"][:100]))
            else:
                results.append(("T3", "问答功能", "❌ 失败", body[:200]))
        
        # T4: 空参数验证
        status, body = http_post(
            f"{BASE}/api/v1/qa/ask",
            {"question": "test"},
            timeout=5
        )
        results.append(("T4", "空参数验证", "✅ 通过" if status == 422 else "❌ 失败", body[:100]))
        
        # T5: 无效 KB ID
        status, body = http_post(
            f"{BASE}/api/v1/qa/ask",
            {"kb_id": "no-such-id", "question": "test"},
            timeout=5
        )
        results.append(("T5", "无效KB ID", "✅ 通过" if status == 404 else "❌ 失败", body[:100]))
    
    # T6: 前端页面
    status, body = http_get(FRONTEND)
    results.append(("T6", "前端页面", "✅ 通过" if status == 200 else "⚠️ 需检查", body[:100]))
    
    # 4. 输出报告
    log("\n=== 测试报告 ===")
    log(f"{'编号':<6} {'测试项':<20} {'状态':<12} {'说明'}")
    log("-" * 80)
    for r in results:
        log(f"{r[0]:<6} {r[1]:<20} {r[2]:<12} {r[3]}")
    
    # 5. 保存报告
    report_path = os.path.join(PROJECT_DIR, "test_report_final.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# SmartDocQA 最终测试报告\n\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| 编号 | 测试项 | 状态 | 说明 |\n")
        f.write("|------|--------|------|------|\n")
        for r in results:
            f.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3][:50]} |\n")
    log(f"\n报告已保存: {report_path}")
    
    # 6. 清理
    log("\n=== 清理 ===")
    backend.terminate()
    log(f"后端已停止 PID={backend.pid}")

if __name__ == "__main__":
    main()
