/**
 * Spinner — 加载动画
 * Props: size (sm|md|lg), className
 */
export function Spinner({ size = 'md', className = '' }) {
  const sizeClass = size === 'sm' ? 'w-4 h-4 border' : size === 'lg' ? 'spinner-lg' : 'w-5 h-5 border'
  return (
    <span className={['spinner inline-block', sizeClass, className].filter(Boolean).join(' ')} />
  )
}

/**
 * 全屏加载遮罩
 */
export function LoadingOverlay({ text = '加载中...' }) {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-bg-base/60 backdrop-blur-sm z-50 animate-fadeIn">
      <div className="flex flex-col items-center gap-4">
        <span className="spinner spinner-lg" />
        {text && <p className="text-sm text-text-secondary">{text}</p>}
      </div>
    </div>
  )
}
