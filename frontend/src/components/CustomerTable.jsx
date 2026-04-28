import { useNavigate } from 'react-router-dom'
import { DataTable } from './ui/DataTable'

// ── 评分徽章 ─────────────────────────────────────────────────────────────────
const gradeBadge = (score) => {
  if (!score && score !== 0) return <span className="badge badge-neutral">-</span>
  if (score >= 80) return <span className="badge badge-success">{score}</span>
  if (score >= 60) return <span className="badge badge-warning">{score}</span>
  return <span className="badge badge-neutral">{score}</span>
}

// ── 跟进状态徽章 — 深紫主题 ───────────────────────────────────────────────
const statusLabel = (status) => {
  const map = {
    NEW:        { text: '新客户',   color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)' },
    CONTACTED:  { text: '已联系',  color: '#60a5fa', bg: 'rgba(96,165,250,0.12)' },
    NEGOTIATING:{ text: '谈判中',  color: '#fbbf24', bg: 'rgba(251,191,36,0.12)' },
    WON:       { text: '已成交',   color: '#34d399', bg: 'rgba(52,211,153,0.12)' },
    LOST:      { text: '已流失',   color: '#f87171', bg: 'rgba(248,113,113,0.12)' },
    INACTIVE:  { text: '已搁置',   color: '#6b7280', bg: 'rgba(255,255,255,0.07)' },
  }
  const s = map[status] || { text: status || '-', color: '#6b7280', bg: 'rgba(255,255,255,0.07)' }
  return (
    <span
      className="badge"
      style={{ color: s.color, background: s.bg }}
    >
      {s.text}
    </span>
  )
}

// ── 优先级指示器 ─────────────────────────────────────────────────────────────
const priorityDot = (p) => {
  const map = {
    HIGH:   { color: '#f87171', label: '高' },
    MEDIUM: { color: '#fbbf24', label: '中' },
    LOW:    { color: '#34d399', label: '低' },
  }
  const { color, label } = map[p] || { color: '#6b7280', label: '-' }
  return (
    <div className="flex items-center gap-2">
      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: color }} />
      <span className="text-[12px] text-text-secondary">{label}</span>
    </div>
  )
}

// ── 可点击链接单元格 ─────────────────────────────────────────────────────────
const LinkCell = ({ href, text }) => {
  if (!text) return <span className="text-text-muted text-[13px]">-</span>
  const url = href || (text.includes('@') ? `mailto:${text}` : (text.startsWith('http') ? text : `https://${text}`))
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="text-accent text-[13px] hover:opacity-75 transition-opacity"
      onClick={(e) => e.stopPropagation()}
    >
      {text}
    </a>
  )
}

// ── 邮箱单元格 ───────────────────────────────────────────────────────────────
const EmailCell = ({ value }) => {
  if (!value) return <span className="text-text-muted text-[13px]">-</span>
  return (
    <a
      href={`mailto:${value}`}
      className="text-accent text-[13px] hover:opacity-75 transition-opacity"
      onClick={(e) => e.stopPropagation()}
    >
      {value}
    </a>
  )
}

// ── 领英单元格 ───────────────────────────────────────────────────────────────
const LinkedInCell = ({ value }) => {
  if (!value) return <span className="text-text-muted text-[13px]">-</span>
  const url = value.startsWith('http') ? value : `https://linkedin.com/in/${value}`
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-1.5 text-[13px] text-[#60a5fa] hover:opacity-75 transition-opacity"
      onClick={(e) => e.stopPropagation()}
    >
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5 shrink-0">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
      </svg>
      领英
    </a>
  )
}

// ── 表格列定义 ───────────────────────────────────────────────────────────────
const columns = [
  {
    key: 'company_name_en',
    label: '公司名称',
    sortable: true,
    render: (_, row) => (
      <div>
        <div className="text-text-primary font-medium text-[13px] max-w-[200px] truncate">
          {row.company_name_en || row.company_name || '-'}
        </div>
        {row.city && (
          <div className="text-text-muted text-[11px] mt-0.5 truncate max-w-[200px]">
            {row.city}
          </div>
        )}
      </div>
    ),
  },
  { key: 'country_name', label: '国家', sortable: true },
  {
    key: 'email',
    label: '邮箱',
    render: (val) => <EmailCell value={val} />,
  },
  { key: 'phone', label: '电话', sortable: true },
  {
    key: 'linkedin_url',
    label: '领英',
    render: (val) => <LinkedInCell value={val} />,
  },
  {
    key: 'website',
    label: '官网',
    render: (val) => (
      <LinkCell href={val} text={val ? val.replace(/^https?:\/\//, '').slice(0, 22) : null} />
    ),
  },
  {
    key: 'background_score',
    label: '评分',
    sortable: true,
    render: (val) => gradeBadge(val),
  },
  {
    key: 'follow_up_status',
    label: '跟进状态',
    render: (val) => statusLabel(val),
  },
  {
    key: 'priority_level',
    label: '优先级',
    render: (val) => priorityDot(val),
  },
  {
    key: 'updated_at',
    label: '更新时间',
    sortable: true,
    render: (val) => (
      <span className="text-text-muted text-[12px] whitespace-nowrap">
        {val ? new Date(val).toLocaleDateString('zh-CN') : '-'}
      </span>
    ),
  },
]

// ── 主组件 ─────────────────────────────────────────────────────────────────
export default function CustomerTable({ customers, loading, onSort, sortField, sortDir }) {
  const navigate = useNavigate()

  const handleRowClick = (row) => {
    navigate(`/customers/${row.id}`)
  }

  return (
    <DataTable
      columns={columns}
      data={customers}
      loading={loading}
      emptyMessage="暂无客户数据"
      onRowClick={handleRowClick}
    />
  )
}
