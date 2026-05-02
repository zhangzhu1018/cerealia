/**
 * Sidebar — 巧克力紫主题 · 左侧固定导航
 */
import { NavLink, useLocation } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/',                  label: '总工作台', icon: 'dashboard' },
  { to: '/customers',         label: '客户管理', icon: 'customers' },
  { to: '/customers/import',  label: '批量导入', icon: 'import' },
  { to: '/emails',            label: '邮件生成', icon: 'email' },
  { to: '/email-settings',    label: '邮件管理', icon: 'emailSettings' },
  { to: '/search',            label: '客户搜索', icon: 'search' },
  { to: '/scoring',           label: '客户评分', icon: 'scoring' },
  { to: '/activities',        label: '操作日志', icon: 'activities' },
]

function Icon({ name, size = 18 }) {
  const paths = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    customers: <><circle cx="9" cy="8" r="4" /><path d="M3 20c0-4 2.7-7 6-7s6 3 6 7" /><circle cx="17" cy="7" r="2.5" /><path d="M21 20c0-2.5-1.5-4.5-3.5-5" /></>,
    import: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></>,
    email: <><rect x="2" y="4" width="20" height="16" rx="2" /><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" /></>,
    emailSettings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></>,
    search: <><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></>,
    activities: <><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></>,
    scoring: <><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></>,
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  )
}

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation()

  return (
    <nav
      style={{ position: 'fixed', top: 0, left: 0, height: '100vh', zIndex: 40 }}
      className={[
        'hidden md:flex',  // 移动端隐藏，md以上显示
        'sidebar bg-bg-sidebar border-r border-border-subtle',
        'flex flex-col',
        collapsed ? 'collapsed' : '',
      ].join(' ')}
    >
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <rect x="2" y="2" width="9" height="9" rx="2" fill="white" />
            <rect x="13" y="2" width="9" height="9" rx="2" fill="white" />
            <rect x="2" y="13" width="9" height="9" rx="2" fill="white" />
            <rect x="13" y="13" width="9" height="9" rx="2" fill="white" />
          </svg>
        </div>
        <span className="sidebar-logo-text">Cerealia</span>
      </div>

      {/* 导航 — 竖排 */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const isActive = item.to === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.to)
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={['nav-item', isActive ? 'active' : ''].join(' ')}
            >
              <span className="nav-item-icon">
                <Icon name={item.icon} size={18} />
              </span>
              <span className="nav-item-label">{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* 底部用户区 */}
      <div className="sidebar-footer">
        <div className="nav-item" style={{ cursor: 'default' }}>
          <div style={{
            width: 28, height: 28, borderRadius: '50%',
            background: 'var(--color-accent)', color: 'var(--color-text-inverse)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, fontWeight: 700, flexShrink: 0,
          }}>张</div>
          <span className="nav-item-label" style={{ fontSize: 12 }}>张竹</span>
        </div>
      </div>
    </nav>
  )
}
