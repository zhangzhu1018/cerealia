import { useState, useEffect, useCallback } from 'react'
import { generateBatchPreview, confirmBatchSend, getCustomers, getEmailAccounts } from '../api'

// 语言选项
const LANGUAGES = [
  { value: 'auto', label: '🇮🇹 Auto（按国家自动推断）' },
  { value: 'en', label: '🇬🇧 English' },
  { value: 'fr', label: '🇫🇷 Français' },
  { value: 'de', label: '🇩🇪 Deutsch' },
  { value: 'it', label: '🇮🇹 Italiano' },
  { value: 'es', label: '🇪🇸 Español' },
  { value: 'pt', label: '🇵🇹 Português' },
  { value: 'ja', label: '🇯🇵 日本語' },
  { value: 'ko', label: '🇰🇷 한국어' },
  { value: 'zh', label: '🇨🇳 中文' },
  { value: 'ar', label: '🇸🇦 العربية' },
  { value: 'ru', label: '🇷🇺 Русский' },
  { value: 'th', label: '🇹🇭 ภาษาไทย' },
  { value: 'vi', label: '🇻🇳 Tiếng Việt' },
  { value: 'tr', label: '🇹🇷 Türkçe' },
  { value: 'pl', label: '🇵🇱 Polski' },
]

// 邮件预览（双栏：英文 + 本地语言）
function EmailPreviewPanel({ preview }) {
  if (!preview) return null
  const lang = preview.language || 'en'
  const langLabel = LANGUAGES.find(l => l.value === lang)?.label?.replace(/^[^ ]+ /, '') || lang.toUpperCase()

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* 英文版 */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-caviar-cream font-display text-sm flex items-center gap-2">
            🇬🇧 English Version
            {preview.ai_generated !== false && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-900/30 text-emerald-400 border border-emerald-700/30">
                AI Generated
              </span>
            )}
          </h4>
        </div>
        <div className="bg-caviar-dark/60 rounded-lg p-4 text-caviar-text text-sm leading-relaxed
          whitespace-pre-wrap max-h-80 overflow-y-auto border border-caviar-sienna/20">
          {preview.body_english}
        </div>
      </div>

      {/* 本地语言版 */}
      {preview.body_local ? (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-caviar-cream font-display text-sm">
              🌐 {langLabel} Version
            </h4>
          </div>
          <div className="bg-caviar-dark/60 rounded-lg p-4 text-caviar-text text-sm leading-relaxed
            whitespace-pre-wrap max-h-80 overflow-y-auto border border-caviar-sienna/20"
            dir={['ar', 'he'].includes(lang) ? 'rtl' : 'ltr'}>
            {preview.body_local}
          </div>
        </div>
      ) : (
        <div className="card flex items-center justify-center text-caviar-muted text-sm">
          无本地语言版本（目标国家使用英语）
        </div>
      )}
    </div>
  )
}

// 单封邮件卡片（列表项）
function EmailCard({ preview, checked, onToggle }) {
  const lang = preview.language || 'en'
  const langLabel = LANGUAGES.find(l => l.value === lang)?.label?.replace(/^[^ ]+ /, '') || lang

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border transition-colors cursor-pointer ${
        checked
          ? 'bg-caviar-gold/5 border-caviar-gold/40'
          : 'bg-caviar-dark/40 border-caviar-sienna/15 hover:border-caviar-cream/20'
      }`}
      onClick={onToggle}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={onToggle}
        onClick={e => e.stopPropagation()}
        className="w-4 h-4 mt-1 flex-shrink-0 rounded border-caviar-sienna/40 bg-caviar-dark accent-caviar-gold cursor-pointer"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-caviar-cream font-medium text-sm truncate">
            {preview.company_name}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-caviar-gold/10 text-caviar-gold">
            {langLabel}
          </span>
          {preview.ai_generated !== false && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-900/30 text-emerald-400">
              AI
            </span>
          )}
        </div>
        {preview.email && (
          <p className="text-caviar-muted text-xs truncate mt-0.5">{preview.email}</p>
        )}
        <p className="text-caviar-muted text-xs mt-1 line-clamp-1">{preview.subject}</p>
      </div>
    </div>
  )
}

export default function EmailPage() {
  const [customers, setCustomers] = useState([])
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [customerLoading, setCustomerLoading] = useState(false)
  const [additionalContext, setAdditionalContext] = useState('')

  // 生成状态
  const [phase, setPhase] = useState('select') // 'select' | 'preview' | 'sending' | 'done'
  const [generating, setGenerating] = useState(false)
  const [previews, setPreviews] = useState([])      // 所有生成的邮件
  const [activePreviewIdx, setActivePreviewIdx] = useState(0) // 当前预览第几个

  // 发送状态
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState(null)
  const [error, setError] = useState('')

  // 账号信息（用于显示）
  const [accounts, setAccounts] = useState([])

  useEffect(() => {
    loadCustomers()
    loadAccounts()
  }, [])

  const loadCustomers = async () => {
    setCustomerLoading(true)
    try {
      const res = await getCustomers({ page_size: 200 })
      const list = res?.data?.items || res?.data || res || []
      // 过滤掉没有邮箱的客户
      const withEmail = list.filter(c => c.email)
      setCustomers(withEmail)
    } catch (err) {
      console.error('加载客户失败', err)
    } finally {
      setCustomerLoading(false)
    }
  }

  const loadAccounts = async () => {
    try {
      const res = await getEmailAccounts()
      setAccounts(Array.isArray(res?.data) ? res.data : [])
    } catch {}
  }

  // ── 客户多选 ────────────────────────────────────────────────────────────────
  const toggleCustomer = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (selectedIds.size === customers.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(customers.map(c => c.id)))
    }
  }

  const selectedCustomers = customers.filter(c => selectedIds.has(c.id))

  // ── 批量生成 ────────────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    if (selectedIds.size === 0) {
      setError('请先选择要发送的客户')
      return
    }
    setGenerating(true)
    setError('')
    setPhase('preview')
    try {
      const res = await generateBatchPreview({
        customers: selectedCustomers.map(c => ({
          company_name_en: c.company_name || c.company_name_en || '',
          country_name: c.country || c.country_name || '',
          email: c.email || '',
          contact_name: c.contact_name || c.contact_name_local || 'Team',
        })),
        additional_context: additionalContext.trim() || undefined,
      })
      const data = res?.data || res
      setPreviews(data.previews || [])
      setActivePreviewIdx(0)
    } catch (err) {
      setError(err.message || '生成失败，请重试')
      setPhase('select')
    } finally {
      setGenerating(false)
    }
  }

  // ── 批量确认发送 ────────────────────────────────────────────────────────────
  const handleConfirmSend = async () => {
    if (previews.length === 0) return
    if (!window.confirm(
      `确定要向 ${previews.length} 家客户发送邮件吗？\n\n` +
      `将向以下邮箱发送：\n${previews.map(p => `• ${p.email}`).slice(0, 5).join('\n')}` +
      (previews.length > 5 ? `\n... 以及其他 ${previews.length - 5} 家` : '')
    )) return

    setSending(true)
    setError('')
    setPhase('sending')
    try {
      const res = await confirmBatchSend({
        previews: previews.map(p => ({
          company_name: p.company_name,
          email: p.email,
          subject: p.subject,
          body_combined: p.body_local
            ? `${p.body_english}\n\n${'─'.repeat(40)}\n${p.language?.toUpperCase()} VERSION\n${'─'.repeat(40)}\n\n${p.body_local}`
            : p.body_english,
          language: p.language,
        })),
      })
      const data = res?.data || res
      setSendResult(data)
      setPhase('done')
    } catch (err) {
      setError(err.message || '发送失败，请重试')
      setPhase('preview')
    } finally {
      setSending(false)
    }
  }

  // ── 重置 ───────────────────────────────────────────────────────────────────
  const handleReset = () => {
    setPhase('select')
    setPreviews([])
    setActivePreviewIdx(0)
    setSendResult(null)
    setError('')
  }

  const activePreview = previews[activePreviewIdx]

  return (
    <div className="space-y-6">

      {/* ── 错误提示 ── */}
      {error && (
        <div className="p-3 bg-red-900/20 border border-red-700/30 rounded-lg text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-xs underline">关闭</button>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          阶段 1：选择客户
      ══════════════════════════════════════════════════════════════ */}
      {phase === 'select' && (
        <div className="space-y-4">
          {/* 说明卡 */}
          <div className="card py-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0">🤖</span>
              <div>
                <h3 className="text-caviar-cream font-display text-base mb-1">AI 双语开发信 · 一键批量发送</h3>
                <p className="text-caviar-muted text-sm">
                  ① 选择客户 → ② DeepSeek AI 为每家生成英文+本地语言开发信 → ③ 预览确认 → ④ 一键发送全部
                </p>
              </div>
            </div>
          </div>

          {/* 补充上下文 */}
          <div className="card">
            <label className="block text-caviar-muted text-xs mb-1.5 uppercase tracking-wide">
              💡 补充上下文（可选）
            </label>
            <textarea
              value={additionalContext}
              onChange={e => setAdditionalContext(e.target.value)}
              rows={2}
              className="input-field w-full resize-none text-sm"
              placeholder="例如：重点突出 HACCP/ISO 认证、48小时手工腌制、已合作米其林餐厅案例..."
            />
          </div>

          {/* 客户选择区 */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-caviar-cream font-display text-sm">
                选择目标客户
                {selectedIds.size > 0 && (
                  <span className="ml-2 text-caviar-gold text-xs">（已选 {selectedIds.size} 家）</span>
                )}
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={toggleAll}
                  className="text-xs text-caviar-muted hover:text-caviar-cream transition-colors underline"
                >
                  {selectedIds.size === customers.length ? '取消全选' : '全选'}
                </button>
                <span className="text-caviar-muted text-xs">
                  共 {customers.length} 家客户（有邮箱）
                </span>
              </div>
            </div>

            {/* 加载状态 */}
            {customerLoading && (
              <div className="text-center py-8 text-caviar-muted">
                <div className="w-6 h-6 border-2 border-caviar-gold border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                加载客户中...
              </div>
            )}

            {/* 客户列表 */}
            {!customerLoading && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-96 overflow-y-auto">
                {customers.map(c => (
                  <div
                    key={c.id}
                    onClick={() => toggleCustomer(c.id)}
                    className={`flex items-start gap-2 p-2.5 rounded-lg border cursor-pointer transition-colors ${
                      selectedIds.has(c.id)
                        ? 'bg-caviar-gold/5 border-caviar-gold/40'
                        : 'bg-caviar-dark/40 border-caviar-sienna/15 hover:border-caviar-cream/20'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.has(c.id)}
                      onChange={() => toggleCustomer(c.id)}
                      className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 rounded border-caviar-sienna/40 bg-caviar-dark accent-caviar-gold cursor-pointer"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-caviar-cream text-xs font-medium truncate">
                        {c.company_name || c.company_name_en}
                      </p>
                      <p className="text-caviar-muted text-[10px] truncate">{c.country || '—'}</p>
                      <p className="text-caviar-muted text-[10px] truncate">{c.email}</p>
                    </div>
                  </div>
                ))}
                {customers.length === 0 && (
                  <div className="col-span-2 text-center py-8 text-caviar-muted text-sm">
                    暂无可发送的客户，请先到「客户管理」添加客户邮箱
                  </div>
                )}
              </div>
            )}

            {/* 生成按钮 */}
            <div className="mt-4 pt-4 border-t border-caviar-sienna/20">
              <button
                onClick={handleGenerate}
                disabled={selectedIds.size === 0 || generating}
                className="btn-primary w-full disabled:opacity-40"
              >
                {generating ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-caviar-ivory border-t-transparent rounded-full animate-spin" />
                    DeepSeek 正在为 {selectedIds.size} 家客户生成双语邮件...
                  </span>
                ) : (
                  <>🤖 生成双语邮件 × {selectedIds.size} 家</>
                )}
              </button>
              {selectedIds.size > 0 && !generating && (
                <p className="text-center text-caviar-muted text-xs mt-2">
                  将使用 DeepSeek 为每家客户生成专属英文+本地语言开发信
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          阶段 2：预览 + 确认发送
      ══════════════════════════════════════════════════════════════ */}
      {(phase === 'preview' || phase === 'sending') && previews.length > 0 && (
        <div className="space-y-4">

          {/* 进度摘要 */}
          <div className="card py-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-3">
                <span className="text-caviar-cream font-display text-sm">
                  📋 邮件预览
                </span>
                <span className="text-caviar-muted text-xs">
                  共 {previews.length} 封 · 正在预览第 {activePreviewIdx + 1} 封
                </span>
                {activePreview?.ai_generated !== false && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-900/30 text-emerald-400 border border-emerald-700/30">
                    🤖 AI 生成
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleReset}
                  disabled={sending}
                  className="text-xs text-caviar-muted hover:text-caviar-cream transition-colors"
                >
                  ← 重新选择客户
                </button>
              </div>
            </div>

            {/* 预览导航 */}
            {previews.length > 1 && (
              <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
                {previews.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => setActivePreviewIdx(i)}
                    className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs border transition-colors ${
                      i === activePreviewIdx
                        ? 'bg-caviar-gold/20 border-caviar-gold/50 text-caviar-gold'
                        : 'bg-caviar-dark/40 border-caviar-sienna/20 text-caviar-muted hover:text-caviar-cream'
                    }`}
                  >
                    {p.company_name?.substring(0, 12)}{p.company_name?.length > 12 ? '…' : ''}
                    {' '}{LANGUAGES.find(l => l.value === p.language)?.label?.match(/^([^ ]+)/)?.[1] || '🌐'}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 当前预览邮件 */}
          {activePreview && (
            <EmailPreviewPanel preview={activePreview} />
          )}

          {/* 发送确认 */}
          {!sending && (
            <div className="card">
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="text-sm text-caviar-muted">
                  <p>确认向 <strong className="text-caviar-gold">{previews.length}</strong> 家客户发送邮件</p>
                  {accounts.length === 0 && (
                    <p className="text-amber-400 text-xs mt-1">
                      ⚠️ 尚未配置发件账号，请先到「邮件管理 → 发件账号」添加 SMTP 账号
                    </p>
                  )}
                </div>
                <button
                  onClick={handleConfirmSend}
                  className="px-6 py-3 rounded-lg bg-caviar-gold/20 border border-caviar-gold/50 text-caviar-gold
                    hover:bg-caviar-gold/30 transition-colors font-medium text-sm
                    disabled:opacity-40"
                  disabled={sending}
                >
                  🚀 确认并发送全部 {previews.length} 封邮件
                </button>
              </div>
            </div>
          )}

          {/* 发送中 */}
          {sending && (
            <div className="card py-6 text-center">
              <div className="w-8 h-8 border-2 border-caviar-gold border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-caviar-gold font-medium">正在批量发送...</p>
              <p className="text-caviar-muted text-xs mt-1">
                真实 SMTP 发送中，请勿关闭页面
              </p>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          阶段 3：发送完成
      ══════════════════════════════════════════════════════════════ */}
      {phase === 'done' && sendResult && (
        <div className="space-y-4">
          <div className="card py-6 text-center">
            <div className="text-4xl mb-3">✅</div>
            <h3 className="text-caviar-gold font-display text-lg mb-2">发送完成！</h3>
            <p className="text-caviar-muted text-sm">
              成功发送 <strong className="text-caviar-gold">{sendResult.sent}</strong> 封，
              失败 <strong className="text-red-400">{sendResult.failed}</strong> 封
            </p>
          </div>

          {/* 失败列表 */}
          {sendResult.failed > 0 && (
            <div className="card">
              <h4 className="text-caviar-cream font-display text-sm mb-3">⚠️ 失败详情</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {(sendResult.results || [])
                  .filter(r => r.status === 'FAILED')
                  .map((r, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-caviar-muted">
                        <strong className="text-caviar-text">{r.company_name}</strong>
                        {' '}{r.email}
                      </span>
                      <span className="text-red-400">{r.reason || '发送失败'}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          <button onClick={handleReset} className="btn-primary w-full">
            ← 继续发送更多客户
          </button>
        </div>
      )}
    </div>
  )
}
