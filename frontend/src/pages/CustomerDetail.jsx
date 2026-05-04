import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ScoringPanel from '../components/ScoringPanel'
import { getCustomer, getScoreHistory, getEmailHistory } from '../api'

// 评分等级徽章
const gradeBadge = (score) => {
  if (!score && score !== 0) return <span className="badge badge-d">-</span>
  if (score >= 80) return <span className="badge badge-a">{score} 分</span>
  if (score >= 60) return <span className="badge badge-b">{score} 分</span>
  if (score >= 40) return <span className="badge badge-c">{score} 分</span>
  return <span className="badge badge-d">{score} 分</span>
}

// 跟进状态
const statusLabel = (status) => {
  const map = {
    NEW:        { text: '新客户',     cls: 'bg-blue-900/30 text-blue-400' },
    CONTACTED:  { text: '已联系',    cls: 'bg-amber-900/30 text-amber-400' },
    NEGOTIATING:{ text: '谈判中',    cls: 'bg-purple-900/30 text-purple-400' },
    WON:        { text: '已成交',    cls: 'bg-emerald-900/30 text-emerald-400' },
    LOST:       { text: '已流失',    cls: 'bg-red-900/30 text-red-400' },
    INACTIVE:   { text: '已搁置',    cls: 'bg-gray-800 text-gray-400' },
  }
  const s = map[status] || { text: status || '-', cls: 'bg-gray-800 text-gray-400' }
  return <span className={`badge ${s.cls}`}>{s.text}</span>
}

// 信息展示字段组件
function InfoField({ label, value, isLink, href }) {
  if (!value && value !== 0) {
    return (
      <div>
        <p className="text-caviar-muted text-xs mb-0.5 uppercase tracking-wide">{label}</p>
        <p className="text-caviar-muted/40 text-sm">-</p>
      </div>
    )
  }
  return (
    <div>
      <p className="text-caviar-muted text-xs mb-0.5 uppercase tracking-wide">{label}</p>
      {isLink && href ? (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-caviar-cream text-sm hover:text-caviar-gold transition-colors underline break-all"
        >
          {value}
        </a>
      ) : (
        <p className="text-caviar-text text-sm break-all">{value}</p>
      )}
    </div>
  )
}

// 社交媒体链接
function SocialMediaLinks({ socialMedia, linkedinUrl }) {
  const platforms = [
    { key: 'facebook',  label: 'Facebook',  color: 'hover:text-blue-500',  icon: <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/> },
    { key: 'instagram',  label: 'Instagram', color: 'hover:text-pink-400',  icon: <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/> },
    { key: 'twitter',    label: 'Twitter/X',  color: 'hover:text-sky-400',  icon: <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/> },
    { key: 'youtube',    label: 'YouTube',    color: 'hover:text-red-500',   icon: <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/> },
    { key: 'tiktok',     label: 'TikTok',     color: 'hover:text-cyan-400',  icon: <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/> },
    { key: 'whatsapp',  label: 'WhatsApp',  color: 'hover:text-green-400', icon: <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/> },
  ]

  const items = []
  if (linkedinUrl) {
    const url = linkedinUrl.startsWith('http') ? linkedinUrl : `https://linkedin.com/in/${linkedinUrl}`
    items.push({ label: 'LinkedIn', url, color: 'hover:text-blue-400', icon: <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/> })
  }
  if (socialMedia) {
    platforms.forEach((p) => {
      if (socialMedia[p.key]) {
        const url = socialMedia[p.key].startsWith('http') ? socialMedia[p.key] : `https://${p.key}.com/${socialMedia[p.key]}`
        items.push({ label: p.label, url, color: p.color, icon: p.icon })
      }
    })
  }

  if (items.length === 0) return <span className="text-caviar-muted/40">-</span>

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <a
          key={item.label}
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className={`flex items-center gap-1.5 text-sm text-caviar-text ${item.color} transition-colors`}
        >
          <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 shrink-0">
            {item.icon}
          </svg>
          {item.label}
        </a>
      ))}
    </div>
  )
}

export default function CustomerDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [customer, setCustomer] = useState(null)
  const [scoreHistory, setScoreHistory] = useState([])
  const [emailHistory, setEmailHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('info')

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true)
      try {
        const [custRes, scoreRes, emailRes] = await Promise.all([
          getCustomer(id).catch(() => null),
          getScoreHistory(id).catch(() => null),
          getEmailHistory(id).catch(() => null),
        ])
        setCustomer(custRes?.data || custRes)
        const scoreData = scoreRes?.data
        setScoreHistory(Array.isArray(scoreData) ? scoreData : scoreData?.scores || [])
        setEmailHistory(Array.isArray(emailRes) ? emailRes : emailRes?.data || [])
      } catch (err) {
        console.error('Failed to load customer:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [id])

  if (loading) {
    return <div className="flex justify-center py-20"><div className="spinner" /></div>
  }

  if (!customer) {
    return (
      <div className="text-center py-20">
        <p className="text-caviar-muted mb-4">客户未找到</p>
        <button onClick={() => navigate('/customers')} className="btn-secondary">
          返回客户列表
        </button>
      </div>
    )
  }

  const latestScore = scoreHistory.length > 0
    ? scoreHistory.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
    : null

  const websiteUrl = customer.website
    ? (customer.website.startsWith('http') ? customer.website : `https://${customer.website}`)
    : null

  return (
    <div className="space-y-6">
      {/* 面包屑 */}
      <div className="flex items-center gap-2 text-sm">
        <button onClick={() => navigate('/customers')} className="text-caviar-muted hover:text-caviar-cream transition-colors">
          客户管理
        </button>
        <span className="text-caviar-muted">/</span>
        <span className="text-caviar-cream">{customer.company_name_en || '-'}</span>
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-1 border-b border-caviar-sienna/30">
        {[
          { key: 'info',    label: '📋 基本信息' },
          { key: 'scoring', label: '⭐ 背调评分' },
          { key: 'history', label: '📝 历史记录' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
              activeTab === tab.key
                ? 'text-caviar-cream border-caviar-cream'
                : 'text-caviar-muted border-transparent hover:text-caviar-cream'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 基本信息 Tab */}
      {activeTab === 'info' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧 */}
          <div className="lg:col-span-2 space-y-4">
            {/* 公司信息卡片 */}
            <div className="card">
              <h3 className="text-caviar-cream font-display text-base mb-4">🏢 公司信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <InfoField label="公司名称（英文）" value={customer.company_name_en} />
                <InfoField label="公司名称（本地）" value={customer.company_name_local} />
                <InfoField label="国家" value={customer.country_name} />
                <InfoField label="城市" value={customer.city} />
                <InfoField label="客户类型" value={customer.customer_type_name} />
                <InfoField label="跟进状态" value={statusLabel(customer.follow_up_status)} />
                <InfoField
                  label="优先级"
                  value={
                    customer.priority_level === 'HIGH' ? '🔴 高' :
                    customer.priority_level === 'MEDIUM' ? '🟡 中' : '🟢 低'
                  }
                />
                <InfoField label="综合评分" value={gradeBadge(customer.background_score)} />
              </div>
              {customer.address && (
                <div className="mt-4 pt-4 border-t border-caviar-sienna/20">
                  <InfoField label="地址" value={customer.address} />
                </div>
              )}
              {customer.notes && (
                <div className="mt-4 pt-4 border-t border-caviar-sienna/20">
                  <p className="text-caviar-muted text-xs mb-1 uppercase tracking-wide">备注</p>
                  <p className="text-caviar-text text-sm whitespace-pre-wrap">{customer.notes}</p>
                </div>
              )}
            </div>

            {/* 联系方式卡片 */}
            <div className="card">
              <h3 className="text-caviar-cream font-display text-base mb-4">📞 联系方式</h3>
              <div className="grid grid-cols-2 gap-4">
                <InfoField label="决策人 / 联系人" value={customer.contact_name} />
                <InfoField
                  label="邮箱"
                  value={customer.email}
                  isLink={!!customer.email}
                  href={customer.email ? `mailto:${customer.email}` : null}
                />
                <InfoField
                  label="电话"
                  value={customer.phone}
                  isLink={!!customer.phone}
                  href={customer.phone ? `tel:${customer.phone}` : null}
                />
                <InfoField
                  label="官网"
                  value={customer.website}
                  isLink={!!websiteUrl}
                  href={websiteUrl}
                />
              </div>
            </div>

            {/* 社交媒体卡片 */}
            <div className="card">
              <h3 className="text-caviar-cream font-display text-base mb-4">🌐 社交媒体</h3>
              <SocialMediaLinks
                linkedinUrl={customer.linkedin_url}
                socialMedia={customer.social_media}
              />
            </div>
          </div>

          {/* 右侧：评分 + 快捷操作 */}
          <div className="space-y-4">
            <div className="card">
              <h3 className="text-caviar-cream font-display text-base mb-3">评分概览</h3>
              {latestScore
                ? <ScoringPanel scoreResult={latestScore} />
                : <p className="text-caviar-muted text-sm text-center py-8">暂无评分记录</p>
              }
            </div>

            <div className="card">
              <h3 className="text-caviar-cream font-display text-base mb-3">快捷操作</h3>
              <div className="space-y-2">
                {customer.email && (
                  <a href={`mailto:${customer.email}`} className="btn-secondary w-full text-center block">
                    ✉️ 发送邮件
                  </a>
                )}
                {websiteUrl && (
                  <a href={websiteUrl} target="_blank" rel="noopener noreferrer"
                    className="btn-secondary w-full text-center block">
                    🌐 访问官网
                  </a>
                )}
                {customer.linkedin_url && (
                  <a
                    href={customer.linkedin_url.startsWith('http') ? customer.linkedin_url : `https://linkedin.com/in/${customer.linkedin_url}`}
                    target="_blank" rel="noopener noreferrer"
                    className="btn-secondary w-full text-center block"
                  >
                    💼 查看领英
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 评分 Tab */}
      {activeTab === 'scoring' && (
        <ScoringPanel scoreResult={latestScore} />
      )}

      {/* 历史记录 Tab */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-caviar-cream font-display text-base mb-4">邮件发送历史</h3>
            {emailHistory.length > 0 ? (
              <div className="space-y-3">
                {emailHistory.map((email, idx) => (
                  <div key={idx} className="p-3 bg-caviar-dark/40 rounded-lg border border-caviar-sienna/15">
                    <div className="flex items-center justify-between">
                      <span className="text-caviar-cream text-sm font-medium">
                        {email.target_language || '英文'} 邮件
                      </span>
                      <span className="text-caviar-muted text-xs">
                        {email.created_at ? new Date(email.created_at).toLocaleDateString('zh-CN') : '-'}
                      </span>
                    </div>
                    {email.subject && (
                      <p className="text-caviar-text text-sm mt-1 font-medium">{email.subject}</p>
                    )}
                    <p className="text-caviar-muted text-xs mt-1 line-clamp-2">
                      {email.english_version || email.content || '-'}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-caviar-muted text-sm text-center py-8">暂无邮件记录</p>
            )}
          </div>

          <div className="card">
            <h3 className="text-caviar-cream font-display text-base mb-4">评分历史</h3>
            {scoreHistory.length > 0 ? (
              <div className="space-y-2">
                {scoreHistory.map((s, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-caviar-dark/40 rounded-lg border border-caviar-sienna/15">
                    <div className="flex items-center gap-3">
                      {gradeBadge(s.total_score || s.background_score)}
                      <span className="text-caviar-cream text-sm">
                        {s.grade && `等级 ${s.grade}`}
                        {(s.total_score || s.background_score) && ` | 评分 ${s.total_score || s.background_score}`}
                      </span>
                    </div>
                    <span className="text-caviar-muted text-xs">
                      {s.created_at ? new Date(s.created_at).toLocaleDateString('zh-CN') : '-'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-caviar-muted text-sm text-center py-8">暂无评分记录</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
