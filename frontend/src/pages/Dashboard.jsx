import StatsDashboard from '../components/StatsDashboard'

export default function Dashboard() {
  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* Hero */}
      <div className="vercel-card" style={{ padding: '32px', marginBottom: 24 }}>
        <span className="vercel-mono">Welcome Back</span>
        <h1 style={{ fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.04em', margin: '8px 0 4px', color: '#171717' }}>
          Cerealia Caviar
        </h1>
        <p style={{ fontSize: 16, color: '#4d4d4d', lineHeight: 1.6, maxWidth: 560 }}>
          Premium sturgeon caviar B2B CRM — 0 additives, 48h hand-crafted, HACCP/ISO certified.
          Exporting to Michelin-star restaurants across Europe, Middle East & Asia.
        </p>
      </div>

      {/* Stats */}
      <StatsDashboard />
    </div>
  )
}
