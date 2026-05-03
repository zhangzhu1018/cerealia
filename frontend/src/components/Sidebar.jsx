/**
 * Sidebar — Vercel white-minimal style
 * Fixed 220px, shadow-border, dark text on white
 */
import { NavLink, useLocation } from 'react-router-dom'

const links = [
  { to: '/', label: '仪表盘' },
  { to: '/customers', label: '客户' },
  { to: '/search', label: '搜索' },
  { to: '/emails', label: '邮件' },
  { to: '/scoring', label: '评分' },
  { to: '/activities', label: '动态' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: 220,
      height: '100vh',
      background: '#ffffff',
      boxShadow: '0 0 0 1px rgba(0,0,0,0.06)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 40,
      fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Logo */}
      <div style={{
        padding: '24px 20px 16px',
        borderBottom: '1px solid #ebebeb',
      }}>
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 14,
          fontWeight: 600,
          color: '#171717',
          letterSpacing: '-0.02em',
        }}>
          CEREALIA
        </span>
        <span style={{
          display: 'block',
          fontSize: 11,
          color: '#808080',
          fontWeight: 400,
          marginTop: 2,
        }}>
          Caviar CRM
        </span>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 12px' }}>
        {links.map(link => {
          const active = location.pathname === link.to
          return (
            <NavLink
              key={link.to}
              to={link.to}
              style={{
                display: 'block',
                padding: '8px 12px',
                marginBottom: 2,
                borderRadius: 6,
                fontSize: 14,
                fontWeight: active ? 500 : 400,
                color: active ? '#171717' : '#666666',
                background: active ? '#fafafa' : 'transparent',
                textDecoration: 'none',
                transition: 'background 0.1s',
              }}
            >
              {link.label}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid #ebebeb',
        fontSize: 11,
        color: '#808080',
      }}>
        v2.0 · PythonAnywhere
      </div>
    </aside>
  )
}
