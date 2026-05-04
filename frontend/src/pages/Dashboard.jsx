import StatsDashboard from '../components/StatsDashboard'

export default function Dashboard() {
  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 32, fontWeight: 300, letterSpacing: '-0.64px', color: '#061b31', margin: '0 0 8px' }}>
          Cerealia Caviar
        </h1>
        <p style={{ fontSize: 16, fontWeight: 300, color: '#64748d', lineHeight: 1.5, maxWidth: 600 }}>
          Premium sturgeon caviar B2B CRM — 0 additives, 48h hand-crafted, HACCP/ISO certified.
          Serving Michelin-star restaurants worldwide.
        </p>
      </div>

      <StatsDashboard />
    </div>
  )
}
