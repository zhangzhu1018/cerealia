# Render 部署详细操作指南

> 目标：在 Render 上部署 Caviar CRM 后端 + MySQL，免费额度可用

---

## 一、前置准备

### 1.1 注册 / 登录 Render
- 访问 [dashboard.render.com](https://dashboard.render.com)
- 用 GitHub 账号登录（最方便）

### 1.2 创建 Render API Key（用于 CLI 部署）
1. 点右上角头像 → **API Keys**
2. 点 **Create API Key**，随便命名如 `caviar-crm`
3. **复制 Key**（格式 `rnb_xxxx`），妥善保存

---

## 二、安装 Render CLI

打开终端，运行：

```bash
npm install -g render-cli
```

登录（粘贴你的 API Key）：

```bash
render-cli login
```

---

## 三、部署（一步完成）

进入项目目录，运行：

```bash
cd /Users/zhangzhu/WorkBuddy/20260425205635/caviar_crm_app
render-cli blueprint deploy --file render.yaml
```

这会自动创建：
- ✅ **caviar-crm-db**（免费 MySQL 数据库）
- ✅ **caviar-crm-backend**（Web 服务）

等待 3~5 分钟，服务全部变绿色即为成功。

---

## 四、配置 DeepSeek API Key

1. 打开 [dashboard.render.com](https://dashboard.render.com)
2. 点击左边栏 **Web Services** → **caviar-crm-backend**
3. 点 **Environment** 标签
4. 滚动到最底部，添加环境变量：

| Key | Value |
|-----|-------|
| `DEEPSEEK_API_KEY` | `sk-xxxxxxxx`（你的 DeepSeek Key） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` |
| `AI_SEARCH_MODEL` | `deepseek-chat` |

5. 点 **Save Changes**（自动触发重新部署）

---

## 五、验证后端是否在线

等部署完成后，访问：

```
https://caviar-crm-backend.onrender.com/api/health
```

看到以下内容即为成功：
```json
{"status":"ok","service":"caviar-crm-backend"}
```

---

## 六、获取后端真实 URL

在 Render Dashboard → caviar-crm-backend → **Settings**，可以看到你的服务 URL，类似：

```
https://caviar-crm-backend-xxxx.onrender.com
```

把这个 URL 发给我，我帮你更新 Netlify 的 `_redirects`，前端就能连上后端了。

---

## 七（可选）：查看 MySQL 数据库

Render Dashboard → **Databases** → **caviar-crm-db** → **Shell**

可以手动执行 `backend/init.sql` 初始化表结构，或者等后端启动时自动建表。

---

## 常见问题

**Q: Blueprint 部署失败怎么办？**
A: 先手动在 Render Dashboard 上创建 MySQL 和 Web 服务，Blueprint 只是自动化，不是唯一方式。

**Q: 免费额度够用吗？**
A: 免费 MySQL（休眠后 90 天数据保留）+ 免费 Web 服务（每月 750 小时），完全够个人使用。

**Q: 后端地址以后会变吗？**
A: Render 免费版如果 15 分钟无活动会休眠，访问时会自动唤醒。URL 不变。
