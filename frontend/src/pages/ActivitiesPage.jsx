import { useState, useEffect } from 'react'
import { getActivities, getActivityStats } from '../api'

const actionIcon = {
  CREATE: '🆕',
  UPDATE: '✏️',
  DELETE: '🗑️',
  SCORE: '⭐',
  EMAIL_SENT: '✉️',
  STATUS_CHANGE: '🔄',
  SCORE_TRIGGER: '⚡',
}

const actionLabel = {
  CREATE: '新建客户',
  UPDATE: '更新客户',
  DELETE: '删除客户',
  SCORE: '背调评分',
  EMAIL_SENT: '发送邮件',
  STATUS_CHANGE: '状态变更',
  SCORE_TRIGGER: '评分触发',
}

const actionColor = {
  CREATE: 'text-emerald-400',
  UPDATE: 'text-blue-400',
  DELETE: 'text-red-400',
  SCORE: 'text-amber-400',
  EMAIL_SENT: 'text-purple-400',
  STATUS_CHANGE: 'text-cyan-400',
  SCORE_TRIGGER: 'text-yellow-400',
}

export default function ActivitiesPage() {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [filter, setFilter] = useState({ action: '', keyword: '' })

  const fetchLogs = async (pageNum = 1) => {
    setLoading(true)
    try {
      const params = { page: pageNum, page_size: 20 }
      if (filter.action) params.action = filter.action
      if (filter.keyword) params.keyword = filter.keyword
      const res = await getActivities(params)
      const data = res.data || res
      setLogs(data.items || [])
      setTotalPages(data.pages || 1)
      setPage(pageNum)
    } catch (err) {
      console.error('Failed to fetch activities:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await getActivityStats()
      setStats(res.data || res)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  useEffect(() => {
    fetchLogs()
    fetchStats()
  }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    fetchLogs(1)
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-caviar-cream font-display text-2xl">操作日志</h2>
          <p className="text-caviar-muted text-sm mt-1">自动记录所有客户操作</p>
        </div>
        {stats && (
          <div className="text-right">
            <div className="text-caviar-cream text-2xl font-display">{stats.total || 0}</div>
            <div className="text-caviar-muted text-xs">总操作数</div>
          </div>
        )}
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          {Object.entries(stats.by_action || {}).map(([action, count]) => (
            <div key={action} className="card p-4 flex items-center gap-3">
              <span className="text-2xl">{actionIcon[action] || '📌'}</span>
              <div>
                <div className="text-caviar-cream font-display text-xl">{count}</div>
                <div className={`text-xs ${actionColor[action] || 'text-caviar-muted'}`}>
                  {actionLabel[action] || action}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 筛选器 */}
      <div className="flex flex-wrap gap-3 items-center">
        <form onSubmit={handleSearch} className="flex gap-2">
          <select
            value={filter.action}
            onChange={(e) => setFilter({ ...filter, action: e.target.value })}
            className="select-field text-sm py-2"
          >
            <option value="">全部操作</option>
            {Object.entries(actionLabel).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <input
            value={filter.keyword}
            onChange={(e) => setFilter({ ...filter, keyword: e.target.value })}
            className="input-field text-sm py-2 w-48"
            placeholder="搜索摘要..."
          />
          <button type="submit" className="btn-primary text-sm py-2">搜索</button>
        </form>
        <button
          onClick={() => { setFilter({ action: '', keyword: '' }); fetchLogs(1) }}
          className="text-xs text-caviar-muted hover:text-caviar-cream transition-colors"
        >
          清除筛选
        </button>
      </div>

      {/* 日志列表 */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="spinner" />
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-16 text-caviar-muted">
            暂无操作记录
          </div>
        ) : (
          <div className="divide-y divide-caviar-sienna/20">
            {logs.map((log) => (
              <div key={log.id} className="px-5 py-4 hover:bg-caviar-sienna/5 transition-colors">
                <div className="flex items-start gap-4">
                  {/* 图标 */}
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-caviar-sienna/20 flex items-center justify-center text-xl mt-0.5">
                    {actionIcon[log.action] || '📌'}
                  </div>

                  {/* 内容 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-sm font-medium ${actionColor[log.action] || 'text-caviar-text'}`}>
                        {actionLabel[log.action] || log.action}
                      </span>
                      {log.customer_id && (
                        <span
                          className="text-xs text-caviar-muted cursor-pointer hover:text-caviar-gold"
                          onClick={() => window.location.href = `/customers/${log.customer_id}`}
                        >
                          #{log.customer_id} {log.customer_name && `· ${log.customer_name}`}
                        </span>
                      )}
                      <span className="text-xs text-caviar-muted/50 ml-auto">
                        {log.created_at && new Date(log.created_at).toLocaleString('zh-CN')}
                      </span>
                    </div>
                    <p className="text-caviar-text text-sm mt-1">{log.summary}</p>
                    {log.detail && (
                      <details className="mt-1">
                        <summary className="text-xs text-caviar-muted cursor-pointer hover:text-caviar-text">
                          详情
                        </summary>
                        <pre className="mt-1 text-xs text-caviar-muted/70 bg-caviar-deep/50 p-2 rounded overflow-x-auto">
                          {typeof log.detail === 'string' ? log.detail : JSON.stringify(JSON.parse(log.detail || '{}'), null, 2)}
                        </pre>
                      </details>
                    )}
                    <div className="flex gap-4 mt-1">
                      <span className="text-xs text-caviar-muted/50">
                        操作者: {log.operator}
                      </span>
                      {log.ip_address && (
                        <span className="text-xs text-caviar-muted/50">
                          IP: {log.ip_address}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => fetchLogs(page - 1)}
            disabled={page <= 1}
            className="btn-primary text-sm disabled:opacity-40"
          >
            上一页
          </button>
          <span className="text-caviar-muted text-sm self-center px-4">
            第 {page} / {totalPages} 页
          </span>
          <button
            onClick={() => fetchLogs(page + 1)}
            disabled={page >= totalPages}
            className="btn-primary text-sm disabled:opacity-40"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  )
}
