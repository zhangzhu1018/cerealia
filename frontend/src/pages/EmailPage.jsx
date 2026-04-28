import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import EmailPreview from '../components/EmailPreview'
import { generateEmail, getCustomers, sendEmailNow, getEmailAccounts } from '../api'

const customerTypes = ['进口商', '批发商', '品牌商', '米其林餐厅', '高端酒店', '零售商', '其他']
const languages = [
  { value: 'english', label: 'English (英文)' },
  { value: 'french', label: 'Français (法文)' },
  { value: 'german', label: 'Deutsch (德文)' },
  { value: 'japanese', label: '日本語 (日文)' },
  { value: 'spanish', label: 'Español (西班牙文)' },
  { value: 'arabic', label: 'العربية (阿拉伯文)' },
]

export default function EmailPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('select') // 'select' | 'manual'
  const [customers, setCustomers] = useState([])
  const [selectedCustomer, setSelectedCustomer] = useState('')
  const [form, setForm] = useState({
    company_name: '',
    customer_type: '',
    target_language: 'french',
    additional_context: '',
  })
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [customerLoading, setCustomerLoading] = useState(false)
  const [sendMsg, setSendMsg] = useState('')

  const handleModeChange = (m) => {
    setMode(m)
    setResult(null)
    setError('')
  }

  const loadCustomers = async () => {
    setCustomerLoading(true)
    try {
      const res = await getCustomers({ page_size: 100 })
      const list = Array.isArray(res) ? res : (res.data?.items || res.data || res.items || [])
      setCustomers(list)
    } catch {
      console.error('Failed to load customers')
    } finally {
      setCustomerLoading(false)
    }
  }

  const handleSelectCustomer = (e) => {
    const id = e.target.value
    setSelectedCustomer(id)
    if (id) {
      const c = customers.find((c) => String(c.id) === id)
      if (c) {
        setForm({
          ...form,
          company_name: c.company_name,
          customer_type: c.customer_type_name || c.customer_type || '',
        })
      }
    }
  }

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const res = await generateEmail({
        company_name: form.company_name,
        customer_type: form.customer_type,
        target_language: form.target_language,
        additional_context: form.additional_context || undefined,
      })
      setResult(res)
    } catch (err) {
      setError(err.message || '生成失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 邮件生成配置 */}
      <div className="card">
        <h3 className="text-caviar-cream font-display text-base mb-4">双语邮件生成</h3>
        <p className="text-caviar-muted text-sm mb-6">
          选择客户或手动输入信息，AI 将自动生成中英双语商务邮件。
        </p>

        {/* 模式切换 */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => handleModeChange('select')}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              mode === 'select'
                ? 'bg-caviar-sienna/30 text-caviar-cream border border-caviar-cream/20'
                : 'text-caviar-muted hover:text-caviar-cream border border-transparent'
            }`}
          >
            选择客户
          </button>
          <button
            onClick={() => handleModeChange('manual')}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              mode === 'manual'
                ? 'bg-caviar-sienna/30 text-caviar-cream border border-caviar-cream/20'
                : 'text-caviar-muted hover:text-caviar-cream border border-transparent'
            }`}
          >
            手动输入
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'select' ? (
            <div>
              <label className="block text-caviar-muted text-xs mb-1.5 uppercase tracking-wide">
                选择客户
              </label>
              <div className="flex gap-3">
                <select
                  value={selectedCustomer}
                  onChange={handleSelectCustomer}
                  onFocus={loadCustomers}
                  className="select-field flex-1 text-sm"
                >
                  <option value="">{customerLoading ? '加载中...' : '点击选择客户'}</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.company_name} · {c.country} · {c.customer_type}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-caviar-muted text-xs mb-1.5 uppercase tracking-wide">
                  公司名称 *
                </label>
                <input
                  name="company_name"
                  value={form.company_name}
                  onChange={handleChange}
                  required
                  className="input-field w-full text-sm"
                  placeholder="客户公司名称"
                />
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1.5 uppercase tracking-wide">
                  客户类型
                </label>
                <select
                  name="customer_type"
                  value={form.customer_type}
                  onChange={handleChange}
                  className="select-field w-full text-sm"
                >
                  <option value="">选择类型</option>
                  {customerTypes.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-caviar-muted text-xs mb-1.5 uppercase tracking-wide">
                目标语言 *
              </label>
              <select
                name="target_language"
                value={form.target_language}
                onChange={handleChange}
                required
                className="select-field w-full text-sm"
              >
                {languages.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-caviar-muted text-xs mb-1.5 uppercase tracking-wide">
              补充上下文（可选）
            </label>
            <textarea
              name="additional_context"
              value={form.additional_context}
              onChange={handleChange}
              rows={3}
              className="input-field w-full resize-none text-sm"
              placeholder="如：重点突出我们的 HACCP/ISO 认证、米其林餐厅合作案例..."
            />
          </div>

          {error && (
            <div className="p-3 bg-red-900/20 border border-red-700/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {sendMsg && (
            <div className="p-3 bg-caviar-sienna/20 border border-caviar-gold/30 rounded-lg text-caviar-gold text-sm">
              {sendMsg}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-50">
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-caviar-ivory border-t-transparent rounded-full animate-spin" />
                生成中...
              </span>
            ) : (
              '✉️ 生成双语邮件'
            )}
          </button>
        </form>

        {/* 立即发送（选中客户时出现） */}
        {result && selectedCustomer && (
          <div className="mt-4 p-4 bg-caviar-sienna/10 border border-caviar-gold/30 rounded-xl">
            <div className="flex items-center justify-between mb-3">
              <p className="text-caviar-gold text-sm font-medium">📤 立即发送到此客户</p>
              <button onClick={() => navigate('/email-settings')}
                className="text-xs text-caviar-muted hover:text-caviar-cream transition-colors">
                批量任务 →
              </button>
            </div>
            <button
              onClick={async () => {
                setSending(true)
                setSendMsg('')
                try {
                  const res = await sendEmailNow({
                    customer_id: parseInt(selectedCustomer),
                    subject: result.subject,
                    content: result.body_combined,
                  })
                  setSendMsg(`✅ ${res.message || '发送成功！请到「邮件管理」查看发送记录'}`)
                } catch (err) {
                  setSendMsg(`❌ 发送失败: ${err.message}（请先到「邮件管理」配置发件账号）`)
                } finally {
                  setSending(false)
                }
              }}
              disabled={sending}
              className="w-full py-2.5 rounded-lg bg-caviar-gold/20 border border-caviar-gold/40 text-caviar-gold hover:bg-caviar-gold/30 transition-colors text-sm font-medium disabled:opacity-50"
            >
              {sending ? '发送中...' : '🚀 真实发送（需配置发件账号）'}
            </button>
          </div>
        )}
      </div>

      {/* 邮件预览 */}
      {result && (
        <div>
          <h3 className="text-caviar-cream font-display text-base mb-4">邮件预览</h3>
          <EmailPreview emailResult={result} />
        </div>
      )}
    </div>
  )
}
