/**
 * Button 组件 — Stripe 风格
 * Props: variant (primary|secondary|ghost|danger), size (sm|md|lg), loading, disabled, icon, children
 */
import { forwardRef } from 'react'

const variants = {
  primary:   'btn-primary',
  secondary: 'btn-secondary',
  ghost:     'btn-ghost',
  danger:    'btn-danger',
}

const sizes = {
  sm: 'btn-sm',
  md: '',
  lg: 'btn-lg',
}

/**
 * @param {{
 *   variant?: 'primary'|'secondary'|'ghost'|'danger',
 *   size?: 'sm'|'md'|'lg',
 *   loading?: boolean,
 *   disabled?: boolean,
 *   icon?: React.ReactNode,
 *   iconRight?: React.ReactNode,
 *   children: React.ReactNode,
 *   className?: string,
 *   ...rest
 * }} props
 */
export const Button = forwardRef(function Button(
  {
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    icon,
    iconRight,
    children,
    className = '',
    ...rest
  },
  ref
) {
  const isDisabled = disabled || loading

  return (
    <button
      ref={ref}
      disabled={isDisabled}
      className={[
        'btn',
        variants[variant] || variants.primary,
        sizes[size] || '',
        loading ? 'cursor-wait opacity-80' : '',
        className,
      ].filter(Boolean).join(' ')}
      {...rest}
    >
      {loading ? (
        <span className="spinner spinner-sm" />
      ) : icon ? (
        <span className="flex-shrink-0 [&>svg]:w-4 [&>svg]:h-4">{icon}</span>
      ) : null}
      {children && <span>{children}</span>}
      {iconRight && !loading && (
        <span className="flex-shrink-0 [&>svg]:w-4 [&>svg]:h-4">{iconRight}</span>
      )}
    </button>
  )
})
