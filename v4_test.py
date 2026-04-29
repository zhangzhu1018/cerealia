import requests, time
BASE='http://localhost:5001/api'
r=requests.post(f'{BASE}/auth/login',json={'email':'JooCerealiaCaviar@gmail.com','password':'caviar2024'},timeout=10)
token=(r.json().get('data') or {}).get('token','')
H={'Authorization':f'Bearer {token}'}
print(f"Login: {r.status_code}, token={token[:16]}...")

r=requests.post(f'{BASE}/emails/generate-batch-preview',headers=H,json={
    'customers':[{'company_name_en':'Petrossian','country_name':'France','email':'','contact_name':''}]
}, timeout=120)
print(f'\nEmail: {r.status_code}')
if r.status_code==200:
    d=r.json().get('data',{}) or {}
    p=d.get('previews',[])
    if p:
        print(f'  ai_generated={p[0].get("ai_generated")}')
        body=(p[0].get('body_english','') or '')[:300]
        print(f'  body: {body[:200]}...')
    else:
        print(f'  NO previews: {str(r.json())[:300]}')
else:
    print(f'  ERROR: {r.text[:300]}')
