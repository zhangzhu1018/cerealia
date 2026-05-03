import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { getDashboardStats } from '../api'

export default function StatsDashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    getDashboardStats().then(r => {
      if (r?.data) setStats(r.data)
    }).catch(() => {})
  }, [])

  if (!stats) return null

  const s = stats

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* Stat cards row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <StatCard label="客户总数" value={s.total_customers ?? 0} />
        <StatCard label="A/B 级" value={s.high_score_count ?? 0} color="#0a72ef" />
        <StatCard label="邮件已发" value={s.emails_sent ?? 0} color="#de1d8d" />
        <StatCard label="搜索中" value={s.active_searches ?? 0} color="#ff5b4f" />
      </div>

      {/* Trend */}
      <div className="vercel-card" style={{ padding: '24px' }}>
        <span className="vercel-mono" style={{ marginBottom: 16, display: 'block' }}>Customer Growth</span>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={[
            { date: '04-26', v: 3 }, { date: '04-27', v: 5 },
            { date: '04-28', v: 8 }, { date: '04-29', v: 12 },
            { date: '04-30', v: 18 }, { date: '05-01', v: 20 },
            { date: '05-02', v: 28 },
          ]}>
            <XAxis dataKey="date" tick={{ fill: '#808080', fontSize: 12 }} axisLine={{ stroke: '#ebebeb' }} />
            <YAxis tick={{ fill: '#808080', fontSize: 12 }} axisLine={{ stroke: '#ebebeb' }} />
            <Tooltip contentStyle={{
              background: '#fff', border: 'none',
              boxShadow: '0 0 0 1px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.08)',
              borderRadius: 8, fontSize: 13, color: '#171717',
            }} />
            <Bar dataKey="v" fill="#171717" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p style={{ fontSize: 12, color: '#808080', textAlign: 'right', marginTop: 12 }}>
          累计 28 家真实客户入库
        </p>
      </div>
    </div>
  )
}

function StatCard({ label, value, color = '#171717' }) {
  return (
    <div className="vercel-card" style={{ padding: '20px' }}>
      <span style={{ fontSize: 12, fontFamily: "'JetBrains Mono', monospace", fontWeight: 500, color: '#808080', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </span>
      <div style={{ fontSize: '2rem', fontWeight: 600, color, letterSpacing: '-0.04em', marginTop: 4, lineHeight: 1 }}>
        {value ?? '—'}
      </div>
    </div>
  )
}
