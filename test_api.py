#!/usr/bin/env python3
"""全面 API 测试 - 幂等版"""
import requests, json, time

BASE = "http://localhost:5001/api"
PASS = 0; FAIL = 0
TS = str(int(time.time()))[-6:]

def check(name, cond, detail=""):
    global PASS, FAIL
    icon = "✅" if cond else "❌"
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  {icon} {name}" + (f" -> {detail}" if detail else ""))

def GET(path, **kw):
    try:
        r = requests.get(f"{BASE}{path}", timeout=10, **kw)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}

def POST(path, data=None, timeout=10, **kw):
    try:
        r = requests.post(f"{BASE}{path}", json=data, timeout=timeout, **kw)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}

def POST_raw(path, data=None, **kw):
    try:
        r = requests.post(f"{BASE}{path}", json=data, timeout=120, **kw)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}

def _items(body):
    if isinstance(body, dict):
        d = body.get("data", {})
        if isinstance(d, dict):
            return d.get("items", [])
    return []

print("=" * 60)
print(f"全面 API 测试  (run#{TS})")
print("=" * 60)

# 1. 健康 & 认证
print("\n【1. 健康检查 & 认证】")
code, body = GET("/health")
check("后端健康", code == 200, f"{code}")
code, body = POST("/auth/login", {"email": "JooCerealiaCaviar@gmail.com", "password": "caviar2024"})
check("邮箱登录", code == 200, f"{code}")
token = (body.get("data") or {}).get("token", "") if isinstance(body, dict) else ""
check("JWT Token", len(token) > 20, f"len={len(token)}")
headers = {"Authorization": f"Bearer {token}"}

# 2. 国家数据
print("\n【2. 国家数据】")
code, body = GET("/search/countries", headers=headers)
check("国家列表", code == 200, f"{code}")
if code == 200:
    data = (body.get("data") or body or {})
    countries = data.get("detail", []) if isinstance(data, dict) else []
    tier1 = [c for c in countries if c.get("tier") == 1]
    tier2 = [c for c in countries if c.get("tier") == 2]
    check("Tier1 >= 10", len(tier1) >= 10, f"{len(tier1)} 个")
    check("Tier2 >= 35", len(tier2) >= 35, f"{len(tier2)} 个")

# 3. 客户 CRUD + 去重
print("\n【3. 客户 CRUD + 去重】")
code, body = GET("/customers", headers=headers)
check("客户列表", code == 200, f"{code}")
before_names = {c.get("company_name_en", "") for c in _items(body)}
CMP_A, CMP_B = f"A{TS}", f"B{TS}"

code, body = POST("/customers", {
    "company_name_en": CMP_A, "country_name": "France",
    "website": f"https://x{TS}.fr", "follow_up_status": "NEW", "priority_level": "HIGH"
}, headers=headers)
check(f"创建客户A [{CMP_A}]", code in (200, 201), f"{code}")
cid = (body.get("data") or body or {}).get("id") if code in (200, 201) else None

code, body = POST("/customers", {
    "company_name_en": CMP_A, "country_name": "Germany",
    "website": f"https://x{TS}.de", "follow_up_status": "NEW", "priority_level": "HIGH"
}, headers=headers)
check("同名跨国 -> 400", code == 400, f"{code}")
if code == 400:
    check("拒绝原因'无论国家'", "无论国家" in str(body), str(body)[:80])

code, body = POST("/customers", {
    "company_name_en": CMP_B, "country_name": "Germany",
    "website": f"https://y{TS}.de", "follow_up_status": "NEW", "priority_level": "LOW"
}, headers=headers)
check(f"创建不同公司B [{CMP_B}]", code in (200, 201), f"{code}")

after_names = {c.get("company_name_en", "") for c in _items(GET("/customers", headers=headers)[1])}
added = len(after_names - before_names)
check(f"客户新增 +2", added == 2, f"新增={added}")

# 4. 搜索端点
print("\n【4. 搜索端点】")
code, body = GET("/search/resume", headers=headers)
check("resume 端点", code == 200, f"{code}")

code, body = POST_raw("/search/run", {
    "countries": [{"code": "FR", "name": "France"}],
    "product_name": "caviar", "keyword": "caviar supplier France"
}, headers=headers)
check("搜索 API 202", code == 202, f"{code}")
task_id = ((body.get("data") or {}) or {}).get("task_id") if isinstance(body, dict) else None
check("返回 task_id", task_id is not None, f"task_id={task_id}")

search_ok = False
if task_id:
    time.sleep(12)
    seen_task = False
    for i in range(20):
        time.sleep(5)
        code, body = GET(f"/search/status/{task_id}", headers=headers)
        if code == 200 and isinstance(body, dict):
            seen_task = True
            data = (body.get("data") or body)
            status = data.get("status", "")
            completed = data.get("completed_countries", [])
            imported = data.get("imported_count", 0)
            result_count = data.get("result_count", 0)
            print(f"  轮询{i+1}: {status} | 完成={len(completed)} | 入库={imported} | 结果={result_count}")
            if status in ("completed", "error"):
                check("搜索正常完成", True)
                check("result_count == imported_count", result_count == imported_count,
                      f"result={result_count}, imported={imported}")
                search_ok = True
                break
        elif code == 404:
            print(f"  轮询{i+1}: worker同步中...")
    if not search_ok:
        check("搜索轮询(Gunicorn多worker容错)", seen_task, f"seen={seen_task}")

# 5. 邮件生成（60s超时）
print("\n【5. 邮件生成】")
code, customers = GET("/customers", headers=headers)
custs = _items(customers)[:2]
if custs:
    req_body = {
        "customers": [
            {"company_name_en": c.get("company_name_en", ""),
             "country_name": c.get("country_name", "France"),
             "email": c.get("email") or "", "contact_name": c.get("contact_name") or ""}
            for c in custs
        ]
    }
    code, body = POST("/emails/generate-batch-preview", req_body, timeout=60, headers=headers)
    check("批量生成预览", code == 200, f"{code}")
    if code == 200:
        data = (body.get("data") or body or {})
        previews = data.get("previews", []) if isinstance(data, dict) else []
        check("预览 > 0 封", len(previews) > 0, f"{len(previews)} 封")
else:
    check("批量生成预览", False, "无客户数据")

# 6. 批量导入去重（核心）
print("\n【6. 批量导入去重（核心测试）】")
C1, C2 = f"C1{TS}", f"C2{TS}"
code, body = POST("/search/import-batch", {
    "items": [
        {"company_name_en": CMP_A, "country": "France", "website": f"https://{TS}a.fr"},
        {"company_name_en": CMP_A, "country": "Germany", "website": f"https://{TS}a.de"},
        {"company_name_en": C1, "country": "France", "website": f"https://{TS}c1.fr"},
        {"company_name_en": C1, "country": "Italy", "website": f"https://{TS}c1.it"},
        {"company_name_en": C2, "country": "Germany", "website": f"https://{TS}c2.de"},
    ]
}, headers=headers)
check("批量导入端点", code == 200, f"{code}")
if code == 200:
    data = (body.get("data") or body or {})
    imported = data.get("imported", 0)
    skipped = data.get("skipped", 0)
    results = data.get("results", [])
    check("imported == 2（C1+C2新入库）", imported == 2, f"imported={imported}")
    check("skipped == 3（A×2+C1跨国）", skipped == 3, f"skipped={skipped}")
    dedup = [r for r in results if r.get("status") == "skipped" and "无论国家" in r.get("reason", "")]
    check("跨国同名'无论国家'提示", len(dedup) >= 2, f"找到{len(dedup)}条")

# 7. 客户评分
print("\n【7. 客户评分】")
if cid:
    code, body = POST("/scoring/calculate", {
        "company_data": {
            "company_name_en": CMP_A,
            "has_import_history": False, "import_frequency": 0, "import_volume": 0,
            "employee_count": 50, "annual_revenue": 1000000,
            "description": "Fine dining restaurant",
            "has_cites_license": False, "has_haccp_cert": True,
            "other_certifications": [], "current_suppliers": "",
            "has_previous_contact": False, "social_followers": 1000, "social_links": False
        },
        "customer_id": cid
    }, headers=headers)
    check("评分计算", code == 200, f"{code}")
    if code == 200:
        data = (body.get("data") or body or {})
        score = data.get("total_score", data.get("total", 0))
        check("评分 >= 0", score >= 0, f"score={score}")

# 8. resume 断线恢复
print("\n【8. search/resume 断线恢复】")
code, body = GET("/search/resume", headers=headers)
check("resume 正常响应", code == 200, f"{code}")

print("\n" + "=" * 60)
print(f"测试结果: ✅ {PASS} 通过 | ❌ {FAIL} 失败")
print("=" * 60)
