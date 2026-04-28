# Caviar CRM 部署指南

> 本地开发环境 → Railway（后端 + MySQL）+ Netlify（前端）

---

## 架构总览

```
Netlify 前端（静态托管）
  https://caviar-crm.netlify.app
  └── /api/*  →  代理到 Railway 后端

Railway 后端（Docker 容器）
  https://caviar-xxx.up.railway.app
  └── MySQL（Railway 插件）
```

---

## 第一步：部署后端（Railway）

### 1.1 创建 Railway 项目

1. 登录 [railway.app](https://railway.app)
2. New Project → **Deploy from GitHub repo**
3. 选择仓库 → Railway 会自动检测 `Dockerfile`

### 1.2 添加 MySQL 数据库

1. 在 Railway 项目中点击 **New** → **Database** → **Add MySQL**
2. Railway 自动创建 MySQL 实例并注入以下环境变量：
   - `MYSQL_HOST`
   - `MYSQL_PORT`
   - `MYSQL_USER`
   - `MYSQL_PASSWORD`
   - `MYSQL_DATABASE`

### 1.3 配置环境变量（必填）

在 Railway 仪表盘中，进入后端服务 → **Variables**，添加：

```
FLASK_ENV = production
SECRET_KEY = <随机强密钥，例如 uuidgen | tr -d '\n'>
CORS_ORIGINS = https://caviar-crm.netlify.app,https://*.netlify.app
```

> `DB_HOST/PORT/USER/PASSWORD/DATABASE` 已由 Railway.toml 自动映射，无需手动填写。

### 1.4 初始化数据库表

Railway 暂不支持自动运行 `init.sql`，需要手动导入：

1. 登录 Railway MySQL（通过 `mysql -h $MYSQL_HOST -u $MYSQL_USER -p $MYSQL_PASSWORD $MYSQL_DATABASE` 或 GUI 工具）
2. 将 `backend/init.sql` 内容粘贴执行

**或者**，在 Railway 容器首次启动时通过 gunicorn 钩子自动建表（需额外代码修改）。

### 1.5 记录后端地址

部署成功后，Railway 会分配一个域名，格式如：

```
https://caviar-xxxx.up.railway.app
```

**复制这个域名**，进入第二步。

---

## 第二步：配置并部署前端（Netlify）

### 2.1 修改 API 代理地址

打开 `frontend/public/_redirects`，将占位符替换为真实 Railway 域名：

```diff
- /api/*        https://YOUR-RAILWAY-URL.railway.app/api/:splat   200
+ /api/*        https://caviar-xxxx.up.railway.app/api/:splat   200
```

同时更新 `netlify.toml` 中的相同位置。

### 2.2 部署到 Netlify

**方式 A：GitHub 持续部署（推荐）**

1. 登录 [app.netlify.com](https://app.netlify.com)
2. New site from Git → 选择仓库
3. Build settings:
   - Build command: `cd frontend && npm run build`
   - Publish directory: `frontend/dist`
4. Deploy site

**方式 B：手动部署 CLI**

```bash
npm install -g netlify-cli
cd caviar_crm_app
netlify deploy --prod --dir=frontend/dist
```

### 2.3 配置自定义域名（可选）

在 Netlify 仪表盘 → Domain management → 添加自定义域名。

---

## 第三步：验证部署

打开前端 URL，测试以下接口：

```
GET https://<railway-url>/api/health
→ {"service":"caviar-crm-backend","status":"ok"}

GET https://<netlify-url>/api/health
→ 应返回相同结果（经由 Netlify 代理）
```

---

## 环境变量速查

### Railway 后端（后端服务）

| 变量名 | 来源 | 说明 |
|--------|------|------|
| `MYSQL_HOST` | Railway MySQL 插件 | 自动注入 |
| `MYSQL_PORT` | Railway MySQL 插件 | 自动注入 |
| `MYSQL_USER` | Railway MySQL 插件 | 自动注入 |
| `MYSQL_PASSWORD` | Railway MySQL 插件 | 自动注入 |
| `MYSQL_DATABASE` | Railway MySQL 插件 | 自动注入 |
| `PORT` | Railway 平台 | 自动注入，默认 ~随机端口 |
| `FLASK_ENV` | 手动配置 | 设为 `production` |
| `SECRET_KEY` | 手动配置 | 随机强密钥 |
| `CORS_ORIGINS` | 手动配置 | 前端域名列表 |

### 本地开发（供参考）

```bash
# .env（项目根目录）
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=caviar2024
DB_NAME=caviar_crm
FLASK_ENV=development
SECRET_KEY=caviar-crm-dev-key
```

---

## 本地 Docker 完整测试

```bash
cd caviar_crm_app

# 启动全套服务（MySQL + 后端 + 前端）
docker-compose up --build

# 前端访问：http://localhost:3000
# 后端 API：http://localhost:5000
```

---

## 故障排查

### 前端 API 请求 404
→ 检查 `frontend/public/_redirects` 中的 Railway 域名是否正确

### 后端启动失败
→ 检查 Railway 仪表盘中 MySQL 变量是否完整注入

### CORS 报错
→ 确认 `CORS_ORIGINS` 包含 Netlify 前端域名

### 数据库表不存在
→ 在 Railway MySQL 中手动执行 `backend/init.sql`
