/**
 * Card / StatCard — Stripe 风格卡片
 */

/**
 * 标准内容卡片
 */
export function Card({ children, className = '', elevated = false, glass = false, onClick, ...rest }) {
  const baseClass = glass ? 'card-glass' : elevated ? 'card-elevated' : 'card'
  return (
    <div
      className={[baseClass, onClick ? 'cursor-pointer' : '', className].filter(Boolean).join(' ')}
      onClick={onClick}
      {...rest}
    >
      {children}
    </div>
  )
}

/**
 * 统计数字卡片（Dashboard 专用）
 * Props: label, value, change, changeType (up|down|neutral), icon
 */
export function StatCard({ label, value, change, changeType = 'neutral', icon, className = '' }) {
  return (
    <div className={['stat-card group', className].filter(Boolean).join(' ')}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="stat-card-label">{label}</p>
          <p className="stat-card-value font-light">{value ?? '—'}</p>
          {change && (
            <p className={[
              'stat-card-change tabular-nums',
              changeType === 'up'   ? 'stat-card-change-up' :
              changeType === 'down' ? 'stat-card-change-down' : 'text-text-secondary'
            ].join(' ')}>
              {change}
            </p>
          )}
        </div>
        {icon && (
          <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-accent-muted flex items-center justify-center text-accent-hover opacity-70 group-hover:opacity-100 transition-opacity">
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
