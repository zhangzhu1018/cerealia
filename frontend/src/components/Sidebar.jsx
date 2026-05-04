import { NavLink, useLocation } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/customers', label: 'Customers' },
  { to: '/search', label: 'Search' },
  { to: '/emails', label: 'Emails' },
  { to: '/scoring', label: 'Scoring' },
  { to: '/activities', label: 'Activity' },
]

export default function Sidebar() {
  const { pathname } = useLocation()

  return (
    <aside style={{
      position: 'fixed', top: 0, left: 0,
      width: 232, height: '100vh',
      background: '#ffffff',
      borderRight: '1px solid #e5edf5',
      display: 'flex', flexDirection: 'column',
      zIndex: 40,
      fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Logo */}
      <div style={{ padding: '28px 24px 20px' }}>
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 15,
          fontWeight: 500,
          color: '#061b31',
          letterSpacing: '-0.01em',
        }}>
          CEREALIA
        </div>
        <div style={{ fontSize: 12, fontWeight: 300, color: '#64748d', marginTop: 3 }}>
          Caviar CRM
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '8px 16px' }}>
        {links.map(l => {
          const active = pathname === l.to
          return (
            <NavLink key={l.to} to={l.to} style={{
              display: 'block',
              padding: '8px 12px',
              marginBottom: 2,
              borderRadius: 6,
              fontSize: 14,
              fontWeight: active ? 400 : 300,
              color: active ? '#533afd' : '#64748d',
              background: active ? 'rgba(83,58,253,0.06)' : 'transparent',
              textDecoration: 'none',
              transition: 'background 0.1s',
            }}>
              {l.label}
            </NavLink>
          )
        })}
      </nav>

      <div style={{
        padding: '16px 24px',
        borderTop: '1px solid #e5edf5',
        fontSize: 11,
        fontWeight: 300,
        color: '#64748d',
      }}>
        PythonAnywhere
      </div>
    </aside>
  )
}
