# Cerealia Caviar CRM 架构评估报告

> 评估日期：2026-04-30 | 评估版本：commit `f1bfa90` | 代码规模：~10,500 行 / 42 关键文件

---

## 一、系统全景

```
┌──────────────────────────┐        ┌──────────────────────────┐        ┌─────────────┐
│   Frontend (React/Vite)  │ serveo │   Backend (Flask)         │        │  MySQL 8.0  │
│                          │ HTTPS  │                          │        │  DeepSeek   │
│  /login → Auth           │ ─────→ │  before_request Guard    │ ─────→ │  SMTP       │
│  /search → AI Search     │        │  7 Blueprints             │        └─────────────┘
│  /customers → CRUD       │        │  6 Services               │
│  /emails → AI生成+发送    │        │  12 Models                │
│  /scoring → 7维评分       │        │  gunicorn --workers 1     │
└──────────────────────────┘        └──────────────────────────┘
```

| 层 | 技术栈 | 文件数 | 行数 |
|----|--------|--------|------|
| 前端 | React 18 + Vite + Tailwind + Recharts | 14 | ~3,500 |
| 后端路由 | Flask Blueprints (7个) | 7 | ~2,600 |
| 后端服务 | Python 服务层 (6个) | 6 | ~2,100 |
| 数据模型 | SQLAlchemy ORM (12表) | 1 | ~400 |
| 基础设施 | Docker Compose + Netlify | 8 | ~230 |
| **合计** | | **~42** | **~10,500** |

---

## 二、数据流

```
【搜索引擎 → 客户池积累 → AI 评分 → AI 邮件外联】

1. SEARCH
   Frontend → POST /api/search/run {keyword, countries}
           → _run_search_async (后台线程)
             → CustomerSearchController.run_full_search()
               → 逐国: _ai_search_companies() via DeepSeek V4 Pro
               → 逐国: _db_save_partial_results() 增量写入 DB
               → progress_callback 更新状态
           → GET /api/search/status/{taskId} 轮询进度
           → completed: 结果自动入库 (is_collected=True)

2. SCORE
   POST /api/scoring/calculate {company_data}
     → 7 维度评分 (100分制):
       import_trade(25) + company_scale(20) + market_position(20)
       + qualification(15) + cooperation_potential(10)
       + social_media(5) + responsiveness(2)
     → Grade: A(85+) B(70+) C(55+) D(40+) E(<40)

3. EMAIL
   POST /api/emails/generate-batch-preview {customers}
     → DeepSeek AI 双语生成 (EN + 本地语言)
     → 150+ 国家语言映射
     → 7 语言硬编码模板降级
   POST /api/emails/confirm-batch-send
     → SMTP 多账户轮询发送
```

---

## 三、搜索模块深度评估

### 3.1 当前架构

```
POST /api/search/run
    │
    ├─ 创建 SearchSession (DB) + _search_tasks (内存)
    ├─ spawn threading.Thread → _run_search_async()
    │     ├─ CustomerSearchController.run_full_search()
    │     │   ├─ Tier 1 (15国): 5 EN + 本地语言 关键词
    │     │   ├─ Tier 2 (44国): 3 EN + 本地语言 关键词
    │     │   └─ Tier 3 (115国): 1 EN 关键词
    │     │
    │     └─ _ai_search_companies() ──→ DeepSeek V4 Pro API
    │         ├─ temperature=0.3, max_tokens=2000
    │         └─ 返回 JSON: [{company_name_en, website, snippet, country}]
    │
    └─ 返回 202 { task_id, status: "pending" }

前端轮询 (1s 间隔, 最多 2 小时):
    GET /api/search/status/{taskId}
      → memory + DB 双读
      → 每 1s 更新 currentCountry / searchProgress
```

### 3.2 关键指标

| 指标 | 之前 | 现在 |
|------|------|------|
| AI 模型 | deepseek-chat | **deepseek-v4-pro** (1M context) |
| 国家数 | 176 (含2重复) | **174** (去重) |
| 单国搜索耗时 | 50-90s | **55-65s** |
| 搜索结果入池 | is_collected=False (不可见) | **is_collected=True** |
| result/imported 一致 | ❌ 不一致 | **✅ 一致** |
| 跨语言去重 | URL 简单比 | **URL + 3词指纹** |
| 前端轮询 | raw fetch (无 auth) | **axios (带 token)** |
| 已入库客户 | 78 家 (FR/IT/JP) | ✅ 真实鱼子酱公司 |

### 3.3 搜索质量评估

**优点**：
- V4 Pro 1M 上下文窗口可处理长结果
- 174 国三级分层策略合理
- 增量入库 + 断线恢复机制完善
- 去重逻辑严密（公司名+URL 双重）

**风险**：
- AI 生成而非网页抓取 — 结果依赖模型训练数据质量
- 缺少网页 URL 验证环节
- 大量 API 调用成本（174 国 × 5-7 关键词/国）

---

## 四、整体架构评分

| 维度 | 评分 | 说明 |
|------|------|------|
| **模块分层** | ⭐⭐⭐⭐⭐ | 路由层 / 服务层 / 模型层分离清晰 |
| **数据流设计** | ⭐⭐⭐⭐ | Search→Import→Score→Email 流水线完整 |
| **错误处理** | ⭐⭐⭐ | 有 try/except 但缺统一错误码 |
| **认证安全** | ⭐⭐⭐ | Token 验证已实现，但 SHA256 无盐 |
| **测试覆盖** | ⭐⭐ | 仅 smoke tests，无单元/集成测试 |
| **可部署性** | ⭐⭐⭐⭐ | Docker + Netlify，但硬编码 URL |
| **可扩展性** | ⭐⭐⭐ | Blueprint 可扩展，但内存状态限单进程 |
| **代码可读性** | ⭐⭐⭐⭐ | 中文注释清晰，函数职责明确 |

---

## 五、已修复问题清单 (P0)

| # | 问题 | 影响 | 修复状态 |
|---|------|------|----------|
| 1 | 页面无登录验证 | 任何人可访问 CRM | ✅ before_request 全局 guard |
| 2 | CORS OPTIONS 被 401 拦截 | 浏览器 Network Error | ✅ OPTIONS 放行 |
| 3 | 搜索 countries dict/string 混用 | `dict.lower()` 崩溃 | ✅ _cn() 统一提取 |
| 4 | 后台线程缺 Flask app context | `RuntimeError: outside context` | ✅ flask_app 参数 + with app.app_context() |
| 5 | _CAVIAR_COUNTRIES 重复国家 | 重复 API 调用 | ✅ 删除 Mongolia/Afghanistan 重复 |
| 6 | is_collected=False | 搜索结果客户池不可见 | ✅ → is_collected=True |
| 7 | result_count ≠ imported_count | 前端显示不一致 | ✅ DB 双读 |
| 8 | 搜索提示词过于泛化 | AI 幻觉公司多 | ✅ REAL/VERIFIABLE + type 字段 |
| 9 | 前端轮询 fetch 无 auth | 请求打不到后端 | ✅ → axios getSearchStatus |
| 10 | stopPolling / 孤儿代码 | 构建失败 | ✅ 提取为 useCallback |
| 11 | 同名跨国未去重 | 同一公司多国重复 | ✅ create_customer + import 统一查重 |
| 12 | country_id NOT NULL | 创建客户 500 | ✅ DB ALTER → NULL |

---

## 六、待修改方案（按优先级）

### P1 — 稳定性（本周）

| # | 项目 | 现状 | 方案 | 工时 |
|---|------|------|------|------|
| 13 | 内存状态迁移 Redis | `_search_tasks` / `_token_store` 单进程 | Redis 存储 + gunicorn workers=4 | 4h |
| 14 | 搜索分页 | 全量结果内存加载 | 后端分页 + 前端懒加载 | 2h |
| 15 | 网页验证 | 无 URL 真实性校验 | HEAD 请求验证 website 可达 | 1h |

### P2 — 质量（本月）

| # | 项目 | 现状 | 方案 | 工时 |
|---|------|------|------|------|
| 16 | 密码安全 | SHA256 无盐 | bcrypt | 1h |
| 17 | 数据库迁移 | `db.create_all()` | Alembic | 3h |
| 18 | 环境变量 | serveo URL 硬编码 | `VITE_API_URL` + Netlify env | 1h |
| 19 | 单元测试 | 无 | pytest + factory_boy | 8h |
| 20 | API 限流 | 无 | Flask-Limiter | 2h |
| 21 | 邮箱模板优化 | 纯文本 | HTML 模板 + 品牌形象 | 2h |

### P3 — 体验（下月）

| # | 项目 | 现状 | 方案 | 工时 |
|---|------|------|------|------|
| 22 | 仪表盘完善 | 基础统计 | 趋势图 + 来源漏斗 | 4h |
| 23 | 客户标签系统 | 无 | tags 字段 UI 管理 | 2h |
| 24 | 邮件追踪 | schema 有字段但未用 | 追踪像素 + webhook | 4h |
| 25 | 多语言 UI | 全中文 | i18next 国际化 | 4h |
| 26 | 移动端适配 | 仅桌面 | 响应式重构 | 4h |

---

## 七、实施路线图

```
Week 1-2 (P1)          Week 3-4 (P2)            Month 2 (P3)
┌─────────────────┐   ┌───────────────────┐    ┌──────────────────┐
│ Redis 状态存储    │   │ bcrypt + Alembic   │    │ 仪表盘趋势图      │
│ gunicorn x4      │   │ pytest 单元测试     │    │ 邮件 HTML 模板    │
│ 搜索分页          │   │ VITE_API_URL      │    │ 邮件追踪像素      │
│ 网页验证 HEAD     │   │ API 限流           │    │ i18n 多语言       │
│                  │   │ 邮箱 HTML 模板      │    │ 移动端适配        │
└─────────────────┘   └───────────────────┘    └──────────────────┘
     稳定基石              工程质量                用户体验
```

---

## 八、搜索模块建议关键词策略

当前搜索使用 AI LLM 直接生成公司列表，建议未来加入：

1. **网页爬虫层**（fallback）：当 AI 返回 website 时，用 `requests.head()` 验证 URL 可达
2. **交叉验证**：同一公司在多个国家/关键词搜索中都出现 → 提高置信度
3. **黑名单**：用户删除的"虚假公司"加入黑名单，后续搜索自动过滤
4. **季节性优化**：鱼子酱旺季（11-12月）优先搜索高消费市场

---

## 九、附录

### A. 关键 API 端点

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | /api/auth/login | 无 | 登录获取 token |
| GET | /api/customers | Bearer | 客户列表（分页） |
| POST | /api/customers | Bearer | 创建客户 |
| POST | /api/search/run | Bearer | 启动搜索 |
| GET | /api/search/status/:id | Bearer | 查询搜索进度 |
| GET | /api/search/countries | 无 | 国家列表（公开） |
| POST | /api/emails/generate-batch-preview | Bearer | AI 生成邮件 |
| POST | /api/scoring/calculate | Bearer | AI 评分 |

### B. 当前部署环境

| 服务 | 地址 | 状态 |
|------|------|------|
| 前端 | https://caviar-crm.netlify.app | ✅ 运行中 |
| 后端 | localhost:5001 (Docker) | ✅ 运行中 |
| 隧道 | serveo.net SSH | ✅ 运行中 |
| 数据库 | MySQL 8.0 (Docker) | ✅ 运行中 |
| AI | DeepSeek V4 Pro | ✅ 已配置 |

### C. 登录凭证

- 邮箱：`JooCerealiaCaviar@gmail.com`
- 密码：`caviar2024`
