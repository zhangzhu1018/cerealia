import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { getDashboardStats } from '../api'

export default function StatsDashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    getDashboardStats().then(r => { if (r?.data) setStats(r.data) }).catch(() => {})
  }, [])

  if (!stats) return null

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        <KpiCard label="Total Customers" value={stats.total_customers ?? 0} />
        <KpiCard label="A/B Grade" value={stats.high_score_count ?? 0} color="#533afd" />
        <KpiCard label="Emails Sent" value={stats.emails_sent ?? 0} color="#15be53" />
        <KpiCard label="Active Searches" value={stats.active_searches ?? 0} color="#64748d" />
      </div>

      {/* Growth Chart */}
      <div className="stripe-card" style={{ padding: 28 }}>
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 11, fontWeight: 500, color: '#64748d',
          textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 20,
        }}>
          Customer Growth · 7 days
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={[
            { d: '04-26', v: 3 },{ d: '04-27', v: 5 },{ d: '04-28', v: 8 },
            { d: '04-29', v: 12 },{ d: '04-30', v: 18 },{ d: '05-01', v: 22 },{ d: '05-02', v: 28 },
          ]}>
            <XAxis dataKey="d" tick={{ fill: '#64748d', fontSize: 11, fontWeight: 300 }} axisLine={{ stroke: '#e5edf5' }} tickLine={false} />
            <YAxis tick={{ fill: '#64748d', fontSize: 11, fontWeight: 300 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{
              background: '#fff', border: '1px solid #e5edf5',
              boxShadow: 'rgba(50,50,93,0.25) 0px 13px 27px -5px, rgba(0,0,0,0.1) 0px 8px 16px -8px',
              borderRadius: 6, fontSize: 13, fontWeight: 300, color: '#061b31',
            }} />
            <Bar dataKey="v" fill="#533afd" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
        <p style={{ fontSize: 12, fontWeight: 300, color: '#64748d', textAlign: 'right', marginTop: 16 }}>
          28 verified caviar companies
        </p>
      </div>
    </div>
  )
}

function KpiCard({ label, value, color = '#061b31' }) {
  return (
    <div className="stripe-card" style={{ padding: '24px 20px' }}>
      <div style={{ fontSize: 11, fontWeight: 500, fontFamily: "'JetBrains Mono', monospace", color: '#64748d', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 36, fontWeight: 300, color, letterSpacing: '-0.03em', lineHeight: 1 }}>
        {value ?? '—'}
      </div>
    </div>
  )
}
