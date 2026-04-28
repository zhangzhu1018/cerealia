import { useState, useEffect } from 'react'
import {
  getEmailAccounts, createEmailAccount, updateEmailAccount,
  deleteEmailAccount, testEmailAccount,
  getEmailTasks, startEmailTask, pauseEmailTask, cancelEmailTask,
  getEmailTaskProgress, getCustomers
} from '../api'

const STATUS_COLORS = {
  DRAFT: 'text-caviar-muted',
  QUEUED: 'text-yellow-400',
  RUNNING: 'text-green-400',
  PAUSED: 'text-orange-400',
  COMPLETED: 'text-caviar-gold',
  CANCELLED: 'text-red-400',
}

const STATUS_LABELS = {
  DRAFT: '草稿',
  QUEUED: '排队中',
  RUNNING: '运行中',
  PAUSED: '已暂停',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
}

export default function EmailSettingsPage() {
  const [tab, setTab] = useState('accounts') // 'accounts' | 'tasks'

  // ── 账号管理 ─────────────────────────────────────────────────────────────
  const [accounts, setAccounts] = useState([])
  const [showAccountForm, setShowAccountForm] = useState(false)
  const [accountForm, setAccountForm] = useState({
    account_name: '', smtp_host: '', smtp_port: 587,
    smtp_user: '', smtp_password: '',
    from_name: 'Cerealia Caviar', from_email: '',
    use_tls: true, daily_limit: 200, is_active: true, priority: 1,
  })
  const [editingAccountId, setEditingAccountId] = useState(null)
  const [accountLoading, setAccountLoading] = useState(false)
  const [accountMsg, setAccountMsg] = useState('')

  // ── 任务管理 ─────────────────────────────────────────────────────────────
  const [tasks, setTasks] = useState([])
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [taskForm, setTaskForm] = useState({
    task_name: '',
    sender_account_id: '',
    target_type: 'ALL_CUSTOMERS',
    target_customer_ids: null,
    subject_template: 'Partnership Opportunity: Premium Chinese Caviar',
    body_template: '',
    language: 'en',
    send_interval_seconds: 30,
    created_by: 'system',
  })
  const [taskLoading, setTaskLoading] = useState(false)
  const [taskMsg, setTaskMsg] = useState('')
  const [pollingTaskId, setPollingTaskId] = useState(null)
  const [taskProgress, setTaskProgress] = useState({})

  useEffect(() => {
    loadAccounts()
    loadTasks()
  }, [])

  // 轮询运行中任务的进度
  useEffect(() => {
    const running = tasks.find(t => t.status === 'RUNNING' || t.status === 'QUEUED')
    if (!running) return
    const interval = setInterval(async () => {
      const p = await getEmailTaskProgress(running.id).catch(() => null)
      if (p) {
        setTaskProgress(prev => ({ ...prev, [running.id]: p.data }))
        if (p.data?.status !== 'RUNNING' && p.data?.status !== 'QUEUED') {
          loadTasks()
        }
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [tasks])

  const loadAccounts = async () => {
    const res = await getEmailAccounts().catch(() => ({ data: [] }))
    setAccounts(Array.isArray(res.data) ? res.data : [])
  }

  const loadTasks = async () => {
    const res = await getEmailTasks().catch(() => ({ data: [] }))
    setTasks(Array.isArray(res.data) ? res.data : [])
  }

  // ── 账号操作 ─────────────────────────────────────────────────────────────

  const openAccountForm = (account = null) => {
    if (account) {
      setEditingAccountId(account.id)
      setAccountForm({
        account_name: account.account_name,
        smtp_host: account.smtp_host,
        smtp_port: account.smtp_port,
        smtp_user: account.smtp_user,
        smtp_password: '',
        from_name: account.from_name,
        from_email: account.from_email,
        use_tls: account.use_tls,
        daily_limit: account.daily_limit,
        is_active: account.is_active,
        priority: account.priority,
      })
    } else {
      setEditingAccountId(null)
      setAccountForm({
        account_name: '', smtp_host: '', smtp_port: 587,
        smtp_user: '', smtp_password: '',
        from_name: 'Cerealia Caviar', from_email: '',
        use_tls: true, daily_limit: 200, is_active: true, priority: 1,
      })
    }
    setShowAccountForm(true)
    setAccountMsg('')
  }

  const submitAccount = async (e) => {
    e.preventDefault()
    setAccountLoading(true)
    setAccountMsg('')
    try {
      if (editingAccountId) {
        await updateEmailAccount(editingAccountId, accountForm)
        setAccountMsg('✅ 账号更新成功')
      } else {
        await createEmailAccount(accountForm)
        setAccountMsg('✅ 账号添加成功')
      }
      await loadAccounts()
      setTimeout(() => setShowAccountForm(false), 1200)
    } catch (err) {
      setAccountMsg(`❌ ${err.message}`)
    } finally {
      setAccountLoading(false)
    }
  }

  const handleDeleteAccount = async (id) => {
    if (!confirm('确认删除该发件账号？')) return
    await deleteEmailAccount(id).catch(err => alert(err.message))
    await loadAccounts()
  }

  const handleTestAccount = async (id) => {
    const email = prompt('请输入测试收件邮箱：')
    if (!email) return
    try {
      const res = await testEmailAccount(id, { test_email: email })
      alert(res.message || '发送成功')
    } catch (err) {
      alert(`发送失败: ${err.message}`)
    }
  }

  // ── 任务操作 ─────────────────────────────────────────────────────────────

  const openTaskForm = () => {
    setTaskForm({
      task_name: '',
      sender_account_id: accounts[0]?.id || '',
      target_type: 'ALL_CUSTOMERS',
      target_customer_ids: null,
      subject_template: 'Partnership Opportunity: Premium Chinese Caviar for Global Importers',
      body_template: '',
      language: 'en',
      send_interval_seconds: 30,
      created_by: 'system',
    })
    setShowTaskForm(true)
    setTaskMsg('')
  }

  const submitTask = async (e) => {
    e.preventDefault()
    setTaskLoading(true)
    setTaskMsg('')
    try {
      const res = await createEmailTask(taskForm)
      const taskId = res.data?.id
      await startEmailTask(taskId)
      setTaskMsg('✅ 任务已创建并启动')
      await loadTasks()
      setTimeout(() => setShowTaskForm(false), 1200)
    } catch (err) {
      setTaskMsg(`❌ ${err.message}`)
    } finally {
      setTaskLoading(false)
    }
  }

  const handleTaskAction = async (id, action) => {
    try {
      if (action === 'start') await startEmailTask(id)
      else if (action === 'pause') await pauseEmailTask(id)
      else if (action === 'cancel') await cancelEmailTask(id)
      await loadTasks()
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-caviar-cream font-display text-xl">📧 邮件管理</h2>
        <div className="flex gap-2 bg-caviar-dark/60 rounded-lg p-1">
          {['accounts', 'tasks'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-md text-sm transition-colors ${
                tab === t ? 'bg-caviar-sienna/30 text-caviar-cream' : 'text-caviar-muted hover:text-caviar-cream'
              }`}>
              {t === 'accounts' ? '📮 发件账号' : '📤 发送任务'}
            </button>
          ))}
        </div>
      </div>

      {/* ── 发件账号 ── */}
      {tab === 'accounts' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button onClick={() => openAccountForm()} className="btn-primary text-sm">
              + 添加发件账号
            </button>
          </div>

          {/* 账号列表 */}
          <div className="grid gap-3">
            {accounts.length === 0 && (
              <div className="card text-center py-8 text-caviar-muted">
                暂无发件账号，请先添加 SMTP 账号
              </div>
            )}
            {accounts.map(acc => (
              <div key={acc.id} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-caviar-cream font-medium text-sm">{acc.account_name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        acc.is_active ? 'bg-green-900/40 text-green-400' : 'bg-gray-800 text-gray-500'
                      }`}>
                        {acc.is_active ? '启用' : '禁用'}
                      </span>
                    </div>
                    <div className="text-caviar-muted text-xs space-y-0.5">
                      <p>SMTP: <span className="text-caviar-text">{acc.smtp_host}:{acc.smtp_port}</span></p>
                      <p>发件人: <span className="text-caviar-text">{acc.from_name} &lt;{acc.from_email}&gt;</span></p>
                      <p>今日已发: <span className="text-caviar-gold">{acc.daily_sent_count || 0} / {acc.daily_limit}</span></p>
                    </div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <button onClick={() => handleTestAccount(acc.id)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-caviar-sienna/20 text-caviar-gold hover:bg-caviar-sienna/30 transition-colors">
                      测试
                    </button>
                    <button onClick={() => openAccountForm(acc)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-caviar-dark/60 text-caviar-muted hover:text-caviar-cream transition-colors">
                      编辑
                    </button>
                    <button onClick={() => handleDeleteAccount(acc.id)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-red-900/20 text-red-400 hover:bg-red-900/30 transition-colors">
                      删除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 账号表单弹窗 */}
          {showAccountForm && (
            <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
              <div className="bg-caviar-deep border border-caviar-sienna/40 rounded-xl w-full max-w-lg p-6 space-y-4">
                <h3 className="text-caviar-cream font-display text-base">
                  {editingAccountId ? '编辑发件账号' : '添加发件账号'}
                </h3>
                {accountMsg && (
                  <div className="p-2 rounded-lg text-sm bg-caviar-dark/80 text-caviar-text">{accountMsg}</div>
                )}
                <form onSubmit={submitAccount} className="space-y-3 text-sm">
                  <div>
                    <label className="block text-caviar-muted text-xs mb-1">账号名称</label>
                    <input className="input-field w-full" value={accountForm.account_name}
                      onChange={e => setAccountForm({...accountForm, account_name: e.target.value})}
                      placeholder="如：主账号sales@cerealia.com" required />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">SMTP 服务器 *</label>
                      <input className="input-field w-full" value={accountForm.smtp_host}
                        onChange={e => setAccountForm({...accountForm, smtp_host: e.target.value})}
                        placeholder="smtp.gmail.com" required />
                    </div>
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">端口 *</label>
                      <input className="input-field w-full" type="number" value={accountForm.smtp_port}
                        onChange={e => setAccountForm({...accountForm, smtp_port: parseInt(e.target.value)})}
                        placeholder="587" required />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">SMTP 用户名 *</label>
                      <input className="input-field w-full" value={accountForm.smtp_user}
                        onChange={e => setAccountForm({...accountForm, smtp_user: e.target.value})}
                        placeholder="your@email.com" required />
                    </div>
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">密码/授权码 *</label>
                      <input className="input-field w-full" type="password" value={accountForm.smtp_password}
                        onChange={e => setAccountForm({...accountForm, smtp_password: e.target.value})}
                        placeholder={editingAccountId ? '留空则不修改' : ''} required={!editingAccountId} />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">发件人名称</label>
                      <input className="input-field w-full" value={accountForm.from_name}
                        onChange={e => setAccountForm({...accountForm, from_name: e.target.value})} />
                    </div>
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">发件地址 *</label>
                      <input className="input-field w-full" value={accountForm.from_email}
                        onChange={e => setAccountForm({...accountForm, from_email: e.target.value})}
                        placeholder="noreply@cerealia.com" required />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">每日上限</label>
                      <input className="input-field w-full" type="number" value={accountForm.daily_limit}
                        onChange={e => setAccountForm({...accountForm, daily_limit: parseInt(e.target.value)})} />
                    </div>
                    <div className="flex items-end gap-3">
                      <label className="flex items-center gap-2 text-caviar-muted text-xs pb-2">
                        <input type="checkbox" checked={accountForm.use_tls}
                          onChange={e => setAccountForm({...accountForm, use_tls: e.target.checked})} />
                        使用 TLS
                      </label>
                      <label className="flex items-center gap-2 text-caviar-muted text-xs pb-2">
                        <input type="checkbox" checked={accountForm.is_active}
                          onChange={e => setAccountForm({...accountForm, is_active: e.target.checked})} />
                        启用
                      </label>
                    </div>
                  </div>
                  <div className="flex gap-3 pt-2">
                    <button type="submit" disabled={accountLoading}
                      className="btn-primary flex-1 disabled:opacity-50">
                      {accountLoading ? '保存中...' : (editingAccountId ? '保存修改' : '添加账号')}
                    </button>
                    <button type="button" onClick={() => setShowAccountForm(false)}
                      className="px-4 py-2 rounded-lg border border-caviar-sienna/40 text-caviar-muted hover:text-caviar-cream transition-colors">
                      取消
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── 发送任务 ── */}
      {tab === 'tasks' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button onClick={openTaskForm}
              className="btn-primary text-sm flex items-center gap-1">
              + 新建发送任务
            </button>
          </div>

          {/* 任务列表 */}
          <div className="grid gap-3">
            {tasks.length === 0 && (
              <div className="card text-center py-8 text-caviar-muted">
                暂无发送任务
              </div>
            )}
            {tasks.map(task => {
              const progress = taskProgress[task.id]
              const pct = progress?.progress_pct ?? (task.total_count > 0
                ? Math.round((task.sent_count + task.failed_count) / task.total_count * 100) : 0)
              return (
                <div key={task.id} className="card">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-caviar-cream font-medium text-sm">{task.task_name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[task.status] || 'text-caviar-muted'}`}
                          style={{ background: 'rgba(0,0,0,0.3)' }}>
                          {STATUS_LABELS[task.status] || task.status}
                        </span>
                      </div>
                      <div className="text-caviar-muted text-xs space-y-0.5">
                        <p>目标: {task.target_type} · 间隔: {task.send_interval_seconds}秒</p>
                        <p>发送账号: {task.sender_account_name || '自动选择'}</p>
                        <p>创建: {task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '-'}</p>
                      </div>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      {task.status === 'RUNNING' && (
                        <button onClick={() => handleTaskAction(task.id, 'pause')}
                          className="text-xs px-3 py-1.5 rounded-lg bg-orange-900/30 text-orange-400 hover:bg-orange-900/40">
                          ⏸ 暂停
                        </button>
                      )}
                      {(task.status === 'DRAFT' || task.status === 'PAUSED') && (
                        <button onClick={() => handleTaskAction(task.id, 'start')}
                          className="text-xs px-3 py-1.5 rounded-lg bg-green-900/30 text-green-400 hover:bg-green-900/40">
                          ▶ 启动
                        </button>
                      )}
                      {['RUNNING', 'QUEUED', 'PAUSED'].includes(task.status) && (
                        <button onClick={() => handleTaskAction(task.id, 'cancel')}
                          className="text-xs px-3 py-1.5 rounded-lg bg-red-900/30 text-red-400 hover:bg-red-900/40">
                          ⏹ 取消
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 进度条 */}
                  {(task.status === 'RUNNING' || task.total_count > 0) && (
                    <div>
                      <div className="flex justify-between text-xs text-caviar-muted mb-1">
                        <span>{task.sent_count || 0} 成功 · {task.failed_count || 0} 失败</span>
                        <span>{pct}%</span>
                      </div>
                      <div className="w-full bg-caviar-dark/60 rounded-full h-2">
                        <div className="bg-caviar-gold rounded-full h-2 transition-all duration-300"
                          style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* 任务表单弹窗 */}
          {showTaskForm && (
            <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 overflow-y-auto">
              <div className="bg-caviar-deep border border-caviar-sienna/40 rounded-xl w-full max-w-lg p-6 space-y-4 my-8">
                <h3 className="text-caviar-cream font-display text-base">新建发送任务</h3>
                {taskMsg && (
                  <div className="p-2 rounded-lg text-sm bg-caviar-dark/80 text-caviar-text">{taskMsg}</div>
                )}
                <form onSubmit={submitTask} className="space-y-3 text-sm">
                  <div>
                    <label className="block text-caviar-muted text-xs mb-1">任务名称 *</label>
                    <input className="input-field w-full" value={taskForm.task_name}
                      onChange={e => setTaskForm({...taskForm, task_name: e.target.value})}
                      placeholder="如：欧洲市场开拓 - 第一批" required />
                  </div>
                  <div>
                    <label className="block text-caviar-muted text-xs mb-1">发件账号</label>
                    <select className="select-field w-full" value={taskForm.sender_account_id}
                      onChange={e => setTaskForm({...taskForm, sender_account_id: e.target.value})}>
                      <option value="">自动选择（轮询）</option>
                      {accounts.map(a => (
                        <option key={a.id} value={a.id}>{a.account_name} ({a.from_email})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-caviar-muted text-xs mb-1">发送目标 *</label>
                    <select className="select-field w-full" value={taskForm.target_type}
                      onChange={e => setTaskForm({...taskForm, target_type: e.target.value})}>
                      <option value="ALL_CUSTOMERS">全部客户（排除近期已发送）</option>
                      <option value="BY_STATUS">按跟进状态筛选</option>
                      <option value="BY_COUNTRY">按国家筛选</option>
                      <option value="BY_IDS">指定客户ID列表</option>
                      <option value="MANUAL">手动输入邮箱列表</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">语言版本</label>
                      <select className="select-field w-full" value={taskForm.language}
                        onChange={e => setTaskForm({...taskForm, language: e.target.value})}>
                        <option value="en">English</option>
                        <option value="fr">Français</option>
                        <option value="de">Deutsch</option>
                        <option value="ja">日本語</option>
                        <option value="es">Español</option>
                        <option value="ar">العربية</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-caviar-muted text-xs mb-1">发送间隔（秒）</label>
                      <input className="input-field w-full" type="number" min="5" max="300"
                        value={taskForm.send_interval_seconds}
                        onChange={e => setTaskForm({...taskForm, send_interval_seconds: parseInt(e.target.value)})} />
                    </div>
                  </div>
                  <div>
                    <label className="block text-caviar-muted text-xs mb-1">邮件主题</label>
                    <input className="input-field w-full" value={taskForm.subject_template}
                      onChange={e => setTaskForm({...taskForm, subject_template: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-caviar-muted text-xs mb-1">邮件正文（支持HTML）</label>
                    <textarea className="input-field w-full resize-none" rows={5}
                      value={taskForm.body_template}
                      onChange={e => setTaskForm({...taskForm, body_template: e.target.value})}
                      placeholder="留空则使用系统默认模板生成双语邮件" />
                  </div>
                  <div className="bg-caviar-sienna/10 rounded-lg p-3 text-xs text-caviar-muted">
                    💡 任务将自动排除近期已发送过的客户。每封邮件间隔 {taskForm.send_interval_seconds} 秒发送。
                    当前每日每账号上限为 {accounts[0]?.daily_limit || 200} 封。
                  </div>
                  <div className="flex gap-3 pt-2">
                    <button type="submit" disabled={taskLoading}
                      className="btn-primary flex-1 disabled:opacity-50">
                      {taskLoading ? '创建中...' : '创建并启动任务'}
                    </button>
                    <button type="button" onClick={() => setShowTaskForm(false)}
                      className="px-4 py-2 rounded-lg border border-caviar-sienna/40 text-caviar-muted hover:text-caviar-cream">
                      取消
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
