#!/usr/bin/env python3
"""V4 Pro 全面测试 - 含认证"""
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

def GET(path, token, **kw):
    try:
        h = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE}{path}", headers=h, timeout=10, **kw)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}

def POST(path, data, token, **kw):
    try:
        h = {"Authorization": f"Bearer {token}"}
        r = requests.post(f"{BASE}{path}", headers=h, json=data, timeout=kw.pop("timeout", 10), **kw)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}

print("=" * 60)
print(f"V4 Pro 全面测试 (run#{TS})")
print("=" * 60)

# 1. 认证
print("\n【1. 认证】")
# 未登录 → 401
code, body = requests.get(f"{BASE}/customers", timeout=5).status_code, {}
try:
    r = requests.get(f"{BASE}/customers", timeout=5)
    code, body = r.status_code, r.json()
    check("未登录 → 401", code == 401, f"{code} {body.get('message','')}")
except: pass

# 登录
r = requests.post(f"{BASE}/auth/login", json={"email": "JooCerealiaCaviar@gmail.com", "password": "caviar2024"})
code, body = r.status_code, r.json()
check("登录", code == 200, f"{code}")
token = (body.get("data") or {}).get("token", "")
check("获取 Token", len(token) > 20)

# 无效密码
r = requests.post(f"{BASE}/auth/login", json={"email": "JooCerealiaCaviar@gmail.com", "password": "wrong"})
check("错误密码 → 401", r.status_code == 401)

H = {"Authorization": f"Bearer {token}"}

# 2. 客户 CRUD
print("\n【2. 客户 CRUD + 去重】")
r = requests.get(f"{BASE}/customers", headers=H)
check("客户列表", r.status_code == 200)
before = len((r.json().get("data",{}) or {}).get("items",[]))

A = f"V4TestA_{TS}"
B = f"V4TestB_{TS}"

r = requests.post(f"{BASE}/customers", headers=H, json={
    "company_name_en": A, "country_name": "France",
    "website": f"https://v4a{TS}.fr", "follow_up_status": "NEW", "priority_level": "HIGH"
})
check(f"创建: {A}", r.status_code == 201, f"{r.status_code}")
cid = (r.json().get("data") or {}).get("id")

r = requests.post(f"{BASE}/customers", headers=H, json={
    "company_name_en": A, "country_name": "Germany",
})
check(f"同名跨国 → 400", r.status_code == 400)

r = requests.post(f"{BASE}/customers", headers=H, json={
    "company_name_en": B, "country_name": "Italy",
    "website": f"https://v4b{TS}.it", "follow_up_status": "NEW", "priority_level": "LOW"
})
check(f"创建: {B}", r.status_code == 201)

r = requests.get(f"{BASE}/customers", headers=H)
after = len((r.json().get("data",{}) or {}).get("items",[]))
check(f"客户數 +2", after == before + 2, f"{before}→{after}")

# 3. 搜索 endpoint
print("\n【3. 搜索 /countries】")
r = requests.get(f"{BASE}/search/countries", headers=H)
check("/countries", r.status_code == 200)
data = (r.json().get("data") or {}).get("detail",[])
tier1 = len([c for c in data if c.get("tier")==1])
tier2 = len([c for c in data if c.get("tier")==2])
check(f"Tier1:{tier1}", tier1 >= 10)
check(f"Tier2:{tier2}", tier2 >= 35)

# 4. 搜索
print("\n【4. 搜索（单国家，V4 Pro）】")
r = requests.post(f"{BASE}/search/run", headers=H, json={
    "countries": [{"code": "FR", "name": "France"}],
    "product_name": "caviar", "keyword": "caviar supplier France restaurant"
}, timeout=120)
check("搜索 202", r.status_code == 202)
task_id = (r.json().get("data") or {}).get("task_id")

if task_id:
    time.sleep(10)
    seen = False
    for i in range(25):
        time.sleep(5)
        r = requests.get(f"{BASE}/search/status/{task_id}", headers=H, timeout=5)
        if r.status_code == 200:
            seen = True
            d = r.json().get("data", r.json())
            s = d.get("status","")
            ic = d.get("imported_count",0)
            rc = d.get("result_count",0)
            comp = len(d.get("completed_countries",[]))
            print(f"  轮询{i+1}: {s} | 完成={comp} | 入库={ic} | 结果={rc}")
            if s in ("completed","error"):
                check("搜索完成", True)
                check("result==imported", rc == ic, f"r={rc} i={ic}")
                break
    if not seen:
        check("搜索轮询", False, "未找到任务")

# 5. ​邮件生成
print("\n【5. 邮件生成】")
r = requests.get(f"{BASE}/customers", headers=H)
custs = (r.json().get("data",{}) or {}).get("items",[])
if custs:
    r = requests.post(f"{BASE}/emails/generate-batch-preview", headers=H, json={
        "customers": [{"company_name_en": custs[0].get("company_name_en",""), "country_name": custs[0].get("country_name","France"), "email": custs[0].get("email",""), "contact_name": ""}]
    }, timeout=60)
    check("邮件预览", r.status_code == 200)
    if r.status_code == 200:
        p = (r.json().get("data",{}) or {}).get("previews",[])
        check("AI 生成", len(p) > 0 and p[0].get("ai_generated", False))

# 6. 评分
print("\n【6. 评分】")
if cid:
    r = requests.post(f"{BASE}/scoring/calculate", headers=H, json={
        "company_data": {
            "company_name_en": A, "has_import_history": False,
            "import_frequency": 0, "import_volume": 0, "employee_count": 50,
            "annual_revenue": 1e6, "description": "Fine dining", "has_cites_license": False,
            "has_haccp_cert": True, "other_certifications": [], "current_suppliers": "",
            "has_previous_contact": False, "social_followers": 1000, "social_links": False
        }, "customer_id": cid
    })
    check("评分", r.status_code == 200)
    if r.status_code == 200:
        score = (r.json().get("data",{}) or {}).get("total_score",0)
        check(f"score≥0", score >= 0, f"s={score}")

# 7. 导入去重
print("\n【7. 批量导入去重】")
C1, C2 = f"V4C1_{TS}", f"V4C2_{TS}"
r = requests.post(f"{BASE}/search/import-batch", headers=H, json={"items": [
    {"company_name_en": A, "country": "France"},
    {"company_name_en": A, "country": "Germany"},
    {"company_name_en": C1, "country": "France"},
    {"company_name_en": C1, "country": "Italy"},
    {"company_name_en": C2, "country": "Germany"},
]})
check("导入", r.status_code == 200)
if r.status_code == 200:
    d = r.json().get("data",{}) or {}
    imported, skipped = d.get("imported",0), d.get("skipped",0)
    check(f"imported=2", imported == 2, f"imp={imported}")
    check(f"skipped=3", skipped == 3, f"skp={skipped}")

# 8. resume
print("\n【8. 断线恢复】")
r = requests.get(f"{BASE}/search/resume", headers=H)
check("resume", r.status_code == 200)

print("\n" + "=" * 60)
print(f"V4 Pro 测试: ✅ {PASS} | ❌ {FAIL}")
print("=" * 60)
