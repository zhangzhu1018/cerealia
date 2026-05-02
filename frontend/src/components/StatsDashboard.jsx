import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { getDashboardStats, getCountryDistribution, getTypeDistribution } from '../api'

// 深紫主题色板 — 紫/青/绿/橙/红
const CHART_COLORS = ['#8b5cf6', '#60a5fa', '#34d399', '#fbbf24', '#f87171', '#a78bfa']

// ── SVG 图标 ────────────────────────────────────────────────────────────────
const IconUsers = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="9" cy="8" r="4" />
    <path d="M3 20c0-4 2.7-7 6-7s6 3 6 7" />
    <circle cx="17" cy="7" r="2.5" />
    <path d="M21 20c0-2.5-1.5-4.5-3.5-5" />
  </svg>
)

const IconStar = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
)

const IconMail = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="20" height="16" rx="2" />
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
  </svg>
)

const IconChart = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
)

// ── 统计卡片 ────────────────────────────────────────────────────────────────
function StatCard({ title, value, subtext, icon, colorClass, iconBg }) {
  return (
    <div className="card p-5 flex items-start gap-4 card-hover">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${colorClass}`} style={{ background: iconBg }}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="stat-card-label">{title}</p>
        <p className="stat-card-value">{value ?? '—'}</p>
        {subtext && <p className="stat-card-change text-text-muted text-[12px] mt-0.5">{subtext}</p>}
      </div>
    </div>
  )
}

// ── 深色 Tooltip ────────────────────────────────────────────────────────────
const DarkTooltip = ({ contentStyle, cursor, ...rest }) => (
  <Tooltip
    {...rest}
    contentStyle={{
      background: '#1f1f35',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '10px',
      color: '#f3f4f6',
      fontSize: '12px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
      ...contentStyle,
    }}
    itemStyle={{ color: '#f3f4f6' }}
    cursor={cursor}
  />
)

// ── 主组件 ─────────────────────────────────────────────────────────────────
export default function StatsDashboard() {
  const [stats, setStats] = useState({
    total_customers: 0,
    high_score_count: 0,
    monthly_emails: 0,
    email_open_rate: 0,
  })
  const [countryData, setCountryData] = useState([])
  const [typeData, setTypeData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getDashboardStats().catch(() => null),
      getCountryDistribution().catch(() => null),
      getTypeDistribution().catch(() => null),
    ]).then(([statsRes, countryRes, typeRes]) => {
      if (statsRes?.data) setStats(statsRes.data)
      if (countryRes?.data) setCountryData(Array.isArray(countryRes.data) ? countryRes.data : [])
      if (typeRes?.data) setTypeData(Array.isArray(typeRes.data) ? typeRes.data : [])
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          title="客户总数"
          value={stats.total_customers}
          icon={<IconUsers />}
          colorClass="text-accent"
          iconBg="rgba(139,92,246,0.15)"
        />
        <StatCard
          title="A/B 级客户"
          value={stats.high_score_count}
          subtext="高潜力客户"
          icon={<IconStar />}
          colorClass="text-warning"
          iconBg="rgba(251,191,36,0.12)"
        />
        <StatCard
          title="本月邮件"
          value={stats.monthly_emails}
          icon={<IconMail />}
          colorClass="text-success"
          iconBg="rgba(52,211,153,0.12)"
        />
        <StatCard
          title="邮件打开率"
          value={stats.email_open_rate > 0 ? `${stats.email_open_rate}%` : '—'}
          subtext="近30天"
          icon={<IconChart />}
          colorClass="text-info"
          iconBg="rgba(96,165,250,0.12)"
        />
      </div>

      {/* 图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 客户国家分布 */}
        <div className="card p-5">
          <h3 className="text-text-primary font-medium text-[14px] mb-4 tracking-tight">客户国家分布</h3>
          {countryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={countryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="count"
                  nameKey="country"
                >
                  {countryData.map((_, index) => (
                    <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <DarkTooltip cursor={{ fill: 'rgba(139,92,246,0.06)' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state h-[260px]">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-10 h-10 text-text-muted mb-2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M8 12h8M12 8v8"/>
              </svg>
              <p className="text-text-muted text-[13px]">暂无数据</p>
            </div>
          )}
        </div>

        {/* 客户类型分布 */}
        <div className="card p-5">
          <h3 className="text-text-primary font-medium text-[14px] mb-4 tracking-tight">客户类型分布</h3>
          {typeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={typeData}>
                <XAxis
                  dataKey="type"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.07)' }}
                />
                <YAxis
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.07)' }}
                />
                <DarkTooltip cursor={{ fill: 'rgba(139,92,246,0.06)' }} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state h-[260px]">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-10 h-10 text-text-muted mb-2">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <path d="M3 9h18M9 21V9"/>
              </svg>
              <p className="text-text-muted text-[13px]">暂无数据</p>
            </div>
          )}
        </div>
      </div>

      {/* 客户增长趋势（模拟数据 + 可用真实 API 替换）*/}
      <div className="card p-5">
        <h3 className="text-text-primary font-medium text-[14px] mb-4 tracking-tight">客户增长趋势（7天）</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={[
            { date: '04-26', 新增: 3 }, { date: '04-27', 新增: 5 },
            { date: '04-28', 新增: 8 }, { date: '04-29', 新增: 12 },
            { date: '04-30', 新增: 18 }, { date: '05-01', 新增: 20 },
            { date: '05-02', 新增: 20 },
          ]}>
            <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={{ stroke: 'rgba(255,255,255,0.07)' }} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={{ stroke: 'rgba(255,255,255,0.07)' }} />
            <DarkTooltip cursor={{ fill: 'rgba(139,92,246,0.06)' }} />
            <Bar dataKey="新增" fill="#34d399" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-text-muted text-[11px] mt-3 text-right">累计 28 家真实客户入库</p>
      </div>
    </div>
  )
}
