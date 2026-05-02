import axios from 'axios'

// 后端服务地址（serveo.net SSH 隧道，需保持隧道进程运行）
// 隧道命令：ssh -R 80:localhost:5001 serveo.net
const BACKEND_URL = 'https://1be7f8a2b839364c-218-104-202-62.serveousercontent.com'

const api = axios.create({
  baseURL: BACKEND_URL + '/api',
  timeout: 600000,   // 10 分钟，避免大搜索结果卡住
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动附加 Authorization token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('caviar_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一返回 response.data（已处理 axios 包装）
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 401 → 清除 token 并跳转登录页
    if (error.response?.status === 401) {
      localStorage.removeItem('caviar_token')
      localStorage.removeItem('caviar_user')
      window.location.href = '/login'
    }
    const msg = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

// ─────────────────────────────────────────────────────────────────────────────
//  统一响应解包辅助
//  后端所有接口返回 { code, data, message } 格式，
//  interceptor 已返回 response.data，函数无需额外处理，直接返回给调用方。
// ─────────────────────────────────────────────────────────────────────────────

// ---------- 客户 ----------
export const getCustomers = (params) => api.get('/customers', { params })
export const getCustomer = (id) => api.get(`/customers/${id}`)
export const createCustomer = (data) => api.post('/customers', data)
export const updateCustomer = (id, data) => api.put(`/customers/${id}`, data)
export const deleteCustomer = (id) => api.delete(`/customers/${id}`)

// ---------- 客户导入 ----------
export const previewImport = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/customers/import/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const importCustomers = (file, { runBackgroundCheck = true, skipDuplicates = true, createdBy = 'import' } = {}) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('run_background_check', String(runBackgroundCheck))
  formData.append('skip_duplicates', String(skipDuplicates))
  formData.append('created_by', createdBy)
  return api.post('/customers/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ---------- 评分 ----------
// calculateScore：POST /scoring/calculate → { code, data: { total_score, grade, ... } }
export const calculateScore = (data) => api.post('/scoring/calculate', data)
// getScoreHistory：GET /scoring/history/:customerId → { code, data: { scores: [...], background_check } }
export const getScoreHistory = (customerId) => api.get(`/scoring/history/${customerId}`)

// ---------- 邮件 ----------
// generateEmail：POST /emails/generate → { code, data: { subject, body_combined, ... } }
export const generateEmail = (data) => api.post('/emails/generate', data)
// 批量生成预览（DeepSeek AI，每家公司一封）
export const generateBatchPreview = (data) => api.post('/emails/generate-batch-preview', data)
// 确认并批量发送（预览OK后一键发送）
export const confirmBatchSend = (data) => api.post('/emails/confirm-batch-send', data)
// getEmailHistory：GET /emails/history/:customerId → { code, data: [{ target_language, created_at, english_version }] }
export const getEmailHistory = (customerId) => api.get(`/emails/history/${customerId}`)
export const sendEmailNow = (data) => api.post('/emails/send-now', data)
export const sendTestEmail = (data) => api.post('/emails/send-test', data)

// ---------- 发件账号 ----------
export const getEmailAccounts = () => api.get('/emails/accounts')
export const createEmailAccount = (data) => api.post('/emails/accounts', data)
export const updateEmailAccount = (id, data) => api.put(`/emails/accounts/${id}`, data)
export const deleteEmailAccount = (id) => api.delete(`/emails/accounts/${id}`)
export const testEmailAccount = (id, data) => api.post(`/emails/accounts/${id}/test`, data)

// ---------- 发送任务 ----------
export const getEmailTasks = () => api.get('/emails/tasks')
export const createEmailTask = (data) => api.post('/emails/tasks', data)
export const getEmailTask = (id) => api.get(`/emails/tasks/${id}`)
export const startEmailTask = (id) => api.post(`/emails/tasks/${id}/start`)
export const pauseEmailTask = (id) => api.post(`/emails/tasks/${id}/pause`)
export const cancelEmailTask = (id) => api.post(`/emails/tasks/${id}/cancel`)
export const getEmailTaskProgress = (id) => api.get(`/emails/tasks/${id}/progress`)
export const getEmailTaskLogs = (id, params) => api.get(`/emails/tasks/${id}/logs`, { params })

// ---------- 搜索 ----------
// 查询搜索任务状态（轮询用）
export const getSearchStatus = (taskId) => api.get(`/search/status/${taskId}`)
// runSearch：POST /search/run → { code, data: { task_id, status, ... } }
export const runSearch = (data) => api.post('/search/run', data)
// getSearchHistory：GET /search/history → { code, data: [{ task_id, status, total_results, ... }] }
export const getSearchHistory = () => api.get('/search/history')
// 批量导入搜索结果到客户池
export const importSearchResults = (items) => api.post('/search/import-batch', { items })
// 查询各国家的搜索状态
export const getSearchProgress = (params) => api.get('/search/progress', { params })
// 重置搜索进度（清除已完成记录）
export const resetSearchProgress = (data) => api.post('/search/reset', data)
// 检查是否有可恢复的搜索会话（断线恢复）
export const checkResume = (params) => api.get('/search/resume', { params })

// ---------- 操作日志 ----------
// getActivities：GET /activities → { code, data: { items, total, pages } }
export const getActivities = (params) => api.get('/activities', { params })
// getActivityStats：GET /activities/stats → { code, data: { by_action, trend_7d, total } }
export const getActivityStats = () => api.get('/activities/stats')

// ---------- 仪表盘 ----------
// getDashboardStats：GET /dashboard/stats → { code, data: { total_customers, high_score_count, monthly_emails, email_open_rate } }
export const getDashboardStats = () => api.get('/dashboard/stats')
// getCountryDistribution：GET /dashboard/country-distribution → { code, data: [{ country, count }] }
export const getCountryDistribution = () => api.get('/dashboard/country-distribution')
// getTypeDistribution：GET /dashboard/type-distribution → { code, data: [{ type, count }] }
export const getTypeDistribution = () => api.get('/dashboard/type-distribution')

export default api
