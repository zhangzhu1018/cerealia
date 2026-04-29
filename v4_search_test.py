import requests, time, json
BASE='http://localhost:5001/api'
r=requests.post(f'{BASE}/auth/login',json={'email':'JooCerealiaCaviar@gmail.com','password':'caviar2024'},timeout=10)
token=(r.json().get('data') or {}).get('token','')
H={'Authorization':f'Bearer {token}'}

r=requests.post(f'{BASE}/search/run',headers=H,json={
    'countries':[{'code':'FR','name':'France'}],
    'product_name':'caviar','keyword':'Petrossian caviar Paris restaurant'
},timeout=30)
print(f'Search: {r.status_code}')
tid=(r.json().get('data',{}) or {}).get('task_id','')
print(f'task_id={tid}')

if tid:
    for i in range(15):
        time.sleep(8)
        r=requests.get(f'{BASE}/search/status/{tid}',headers=H,timeout=10)
        if r.status_code==200:
            d=r.json().get('data',r.json())
            s=d.get('status','')
            ic=d.get('imported_count',0)
            rc=d.get('result_count',0)
            comp=len(d.get('completed_countries',[]))
            print(f'  [{i+1}] {s} | done={comp} | imported={ic} | result={rc}')
            if s in ('completed','error'):
                if s=='completed':
                    print(f'\n  ✅ 搜索完成! 导入 {ic} 条新客户')
                    # 显示搜索结果摘要
                    results=d.get('results',[])
                    for j,r in enumerate(results[:5]):
                        print(f'  {j+1}. {r.get("company_name_en","?")} ({r.get("website","?")})')
                break
        elif r.status_code==404:
            print(f'  [{i+1}] 404')
else:
    print('No task_id')
