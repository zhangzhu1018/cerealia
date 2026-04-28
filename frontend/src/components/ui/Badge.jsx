/**
 * Badge / StatusDot — 徽章与状态指示器
 */

/**
 * 状态徽章
 * Props: variant (accent|gold|success|warning|error|muted), children, dot
 */
export function Badge({ variant = 'muted', children, dot = false, className = '' }) {
  return (
    <span className={['badge', `badge-${variant}`, className].filter(Boolean).join(' ')}>
      {dot && (
        <span className={[
          'status-dot flex-shrink-0',
          variant === 'success' ? 'status-dot-success' :
          variant === 'warning' ? 'status-dot-warning' :
          variant === 'error'   ? 'status-dot-error'   : 'status-dot-muted'
        ].join(' ')} />
      )}
      {children}
    </span>
  )
}

/**
 * 独立状态点
 */
export function StatusDot({ status = 'muted', className = '' }) {
  return (
    <span
      className={[
        'status-dot inline-block',
        status === 'success' ? 'status-dot-success' :
        status === 'warning' ? 'status-dot-warning' :
        status === 'error'   ? 'status-dot-error'   : 'status-dot-muted',
        className,
      ].filter(Boolean).join(' ')}
    />
  )
}
