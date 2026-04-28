/**
 * FormControls — Input / Textarea / Select — 深紫主题
 */
import { forwardRef } from 'react'

// ── Input ────────────────────────────────────────────────────────────────────
export const Input = forwardRef(function Input(
  { label, error, hint, prefix, suffix, className = '', containerClassName = '', ...rest },
  ref
) {
  return (
    <div className={['form-group', containerClassName].filter(Boolean).join(' ')}>
      {label && <label className="form-label">{label}</label>}
      <div className="relative flex items-center">
        {prefix && (
          <span className="absolute left-3 text-text-muted flex-shrink-0 [&>svg]:w-4 [&>svg]:h-4">
            {prefix}
          </span>
        )}
        <input
          ref={ref}
          className={[
            'form-input',
            error ? '!border-danger focus:!border-danger' : '',
            prefix ? '!pl-9' : '',
            suffix ? '!pr-9' : '',
            className,
          ].filter(Boolean).join(' ')}
          {...rest}
        />
        {suffix && (
          <span className="absolute right-3 text-text-muted flex-shrink-0 [&>svg]:w-4 [&>svg]:h-4">
            {suffix}
          </span>
        )}
      </div>
      {error && <p className="form-hint !text-danger">{error}</p>}
      {hint && !error && <p className="form-hint">{hint}</p>}
    </div>
  )
})

// ── Textarea ─────────────────────────────────────────────────────────────────
export const Textarea = forwardRef(function Textarea(
  { label, error, hint, className = '', containerClassName = '', ...rest },
  ref
) {
  return (
    <div className={['form-group', containerClassName].filter(Boolean).join(' ')}>
      {label && <label className="form-label">{label}</label>}
      <textarea
        ref={ref}
        className={[
          'form-textarea',
          error ? '!border-danger focus:!border-danger' : '',
          className,
        ].filter(Boolean).join(' ')}
        {...rest}
      />
      {error && <p className="form-hint !text-danger">{error}</p>}
      {hint && !error && <p className="form-hint">{hint}</p>}
    </div>
  )
})

// ── Select ───────────────────────────────────────────────────────────────────
export const Select = forwardRef(function Select(
  { label, error, hint, options = [], placeholder, className = '', containerClassName = '', ...rest },
  ref
) {
  return (
    <div className={['form-group', containerClassName].filter(Boolean).join(' ')}>
      {label && <label className="form-label">{label}</label>}
      <select
        ref={ref}
        className={[
          'form-select',
          error ? '!border-danger focus:!border-danger' : '',
          className,
        ].filter(Boolean).join(' ')}
        {...rest}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error && <p className="form-hint !text-danger">{error}</p>}
      {hint && !error && <p className="form-hint">{hint}</p>}
    </div>
  )
})
