/**
 * EmptyState — 空状态组件
 * Props: icon (SVG component), title, description, action (ReactNode)
 */
export function EmptyState({ icon, title, description, action, className = '' }) {
  return (
    <div className={['empty-state', className].filter(Boolean).join(' ')}>
      {icon && (
        <div className="empty-state-icon">{icon}</div>
      )}
      {title && <h3>{title}</h3>}
      {description && <p>{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

// 预设空状态 SVG 图标
EmptyState.Icons = {
  Search: () => (
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="21" cy="21" r="14" />
      <path d="m33 33 9 9" strokeLinecap="round" />
      <path d="M21 14v7l4 4" strokeLinecap="round" />
    </svg>
  ),
  Users: () => (
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="20" cy="16" r="7" />
      <path d="M5 40c0-8 6.7-14 15-14s15 6 15 14" strokeLinecap="round" />
      <path d="M33 14c2.8 0 5 2.2 5 5s-2.2 5-5 5-5-2.2-5-5 2.2-5 5-5z" />
      <path d="M39 33c1.7 1.3 3 4 3 7" strokeLinecap="round" />
    </svg>
  ),
  Inbox: () => (
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M8 12h32v24H8z" strokeLinejoin="round" />
      <path d="M8 12 24 26l16-14" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  File: () => (
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M12 8h16l10 10v26H12V8z" strokeLinejoin="round" />
      <path d="M28 8v10h10" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M18 24h12M18 31h8" strokeLinecap="round" />
    </svg>
  ),
}
