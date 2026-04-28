# Cerealia Caviar CRM Backend

鲟鱼子酱外贸 CRM 系统 Flask REST API

## 快速启动

```bash
cd caviar_crm_app

# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 MySQL 连接信息

# 4. 启动开发服务器
python -m backend.app
# 或
flask --app backend.app run --debug
# 或（生产环境）
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

## 环境变量

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=caviar_crm
FLASK_ENV=development
SECRET_KEY=your-secret-key
CORS_ORIGINS=*
```

## API 路由一览

### 客户管理 `/api/customers`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/customers | 分页+筛选列表 |
| POST | /api/customers | 新建客户 |
| GET | /api/customers/\<id\> | 获取客户详情 |
| PUT | /api/customers/\<id\> | 更新客户 |
| DELETE | /api/customers/\<id\> | 删除客户 |
| POST | /api/customers/import/preview | 预览 Excel/CSV（自动列映射） |
| POST | /api/customers/import | 批量导入（Excel/CSV） |

### 背调评分 `/api/scoring`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/scoring/calculate | 计算背调评分 |
| POST | /api/scoring/batch | 批量计算评分 |
| GET | /api/scoring/history/\<id\> | 客户评分历史 |

### 邮件生成 `/api/emails`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/emails/generate | 生成双语邮件 |
| GET | /api/emails/templates | 模板列表 |
| POST | /api/emails/templates | 创建模板 |
| POST | /api/emails/send | 记录发送 |
| GET | /api/emails/logs/\<id\> | 发送历史 |
| POST | /api/emails/send-now | 实时发送（真实SMTP） |
| POST | /api/emails/send-test | 发送测试邮件 |

### 发件账号 `/api/emails/accounts`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/emails/accounts | 账号列表 |
| POST | /api/emails/accounts | 添加账号 |
| PUT | /api/emails/accounts/\<id\> | 更新账号 |
| DELETE | /api/emails/accounts/\<id\> | 删除账号 |
| POST | /api/emails/accounts/\<id\>/test | 测试连通性 |

### 发送任务 `/api/emails/tasks`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/emails/tasks | 任务列表 |
| POST | /api/emails/tasks | 创建任务 |
| GET | /api/emails/tasks/\<id\> | 任务详情 |
| POST | /api/emails/tasks/\<id\>/start | 启动任务 |
| POST | /api/emails/tasks/\<id\>/pause | 暂停任务 |
| POST | /api/emails/tasks/\<id\>/cancel | 取消任务 |
| GET | /api/emails/tasks/\<id\>/progress | 轮询进度 |
| GET | /api/emails/tasks/\<id\>/logs | 任务发送记录 |

### 客户搜索 `/api/search`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/search/run | 按国家触发爬虫 |
| POST | /api/search/run-by-name | 按公司名搜索 |
| GET | /api/search/status/\<id\> | 任务状态查询 |
| GET | /api/search/countries | 可搜索国家列表 |

## 数据模型

- `Country` — 国家字典
- `CustomerType` — 客户类型（进口商/批发商/米其林餐厅等）
- `Customer` — 客户主表（含 7 项评分字段）
- `BackgroundCheck` — 背调详细信息
- `EmailTemplate` — 邮件模板
- `EmailSentLog` — 邮件发送记录
- `EmailAccount` — 发件邮箱账号（支持多账号轮询）
- `EmailTask` — 批量邮件发送任务
- `FollowUpTask` — 跟进任务
- `StatisticsDaily` — 每日统计
- `ActivityLog` — 操作日志

## 技术栈

- Flask 3.0 + Flask-SQLAlchemy
- MySQL 8.0 (utf8mb4)
- Flask-CORS
- PyMySQL
- 爬虫：requests + BeautifulSoup4 + fake-useragent
