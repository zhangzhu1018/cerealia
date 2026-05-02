# PythonAnywhere 部署指南

## 1. 注册
https://www.pythonanywhere.com → Create Beginner Account (免费)

## 2. 上传代码
```bash
# 在 PythonAnywhere Bash Console 执行:
git clone https://github.com/zhangzhu1018/cerealia.git caviar-crm
cd caviar-crm
pip install -r requirements.txt
```

## 3. 配置 Web App
- Web tab → "Add a new web app" → Flask → Python 3.11
- WSGI file 内容替换为 deploy/wsgi.py
- 修改 `YOUR_USERNAME` 为你的 PythonAnywhere 用户名

## 4. 配置 MySQL
```bash
# 在 PythonAnywhere MySQL 标签创建数据库
# 数据库名: YOUR_USERNAME$caviar_crm
```

## 5. 环境变量
在 Web tab → Virtualenv 设置:
- FLASK_ENV=production
- DEEPSEEK_API_KEY=sk-b969d8e7c3d84ee8bd499170d6e52eaa
- DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
- DB_HOST=YOUR_USERNAME.mysql.pythonanywhere-services.com
- DB_USER=YOUR_USERNAME
- DB_PASSWORD=你的MySQL密码
- DB_NAME=YOUR_USERNAME$caviar_crm

## 6. 获取固定 URL
你的后端地址: https://YOUR_USERNAME.pythonanywhere.com
