import { useState } from 'react'

export default function EmailPreview({ emailResult }) {
  const [copied, setCopied] = useState('')

  if (!emailResult) {
    return (
      <div className="card flex items-center justify-center h-64 text-caviar-muted">
        请先生成邮件
      </div>
    )
  }

  const { english_version, target_version } = emailResult

  const copyToClipboard = async (text, label) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(label)
      setTimeout(() => setCopied(''), 2000)
    } catch {
      // fallback
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(label)
      setTimeout(() => setCopied(''), 2000)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 英文版 */}
      <div className="card relative">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-caviar-cream font-display text-sm">English Version</h4>
          <button
            onClick={() => copyToClipboard(english_version, 'en')}
            className="text-xs text-caviar-muted hover:text-caviar-cream transition-colors"
          >
            {copied === 'en' ? '✅ 已复制' : '📋 复制'}
          </button>
        </div>
        <div className="bg-caviar-dark/60 rounded-lg p-4 text-caviar-text text-sm leading-relaxed
          whitespace-pre-wrap max-h-96 overflow-y-auto border border-caviar-sienna/20">
          {english_version}
        </div>
      </div>

      {/* 目标语言版 */}
      <div className="card relative">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-caviar-cream font-display text-sm">
            {emailResult.target_language || '目标语言'} Version
          </h4>
          <button
            onClick={() => copyToClipboard(target_version, 'target')}
            className="text-xs text-caviar-muted hover:text-caviar-cream transition-colors"
          >
            {copied === 'target' ? '✅ 已复制' : '📋 复制'}
          </button>
        </div>
        <div className="bg-caviar-dark/60 rounded-lg p-4 text-caviar-text text-sm leading-relaxed
          whitespace-pre-wrap max-h-96 overflow-y-auto border border-caviar-sienna/20">
          {target_version}
        </div>
      </div>
    </div>
  )
}
