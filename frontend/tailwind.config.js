/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],

  theme: {
    extend: {
      /* ── 字体 ─────────────────────────────────────────── */
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },

      /* ── 深紫颜色体系 ─────────────────────────────── */
      colors: {
        /* 背景层 */
        'bg-base':     '#13131f',
        'bg-surface':  '#1a1a2e',
        'bg-card':     '#1f1f35',
        'bg-card-hover': '#252542',
        'bg-input':    '#16162a',
        'bg-sidebar':  '#13131f',
        'bg-modal':    '#1f1f35',

        /* 文字 */
        'text-primary':   '#f3f4f6',
        'text-secondary': '#9ca3af',
        'text-muted':     '#6b7280',

        /* 强调色 — 亮紫 */
        'accent':        '#8b5cf6',
        'accent-hover':  '#7c3aed',
        'accent-light':  'rgba(139,92,246,0.15)',
        'accent-ring':   'rgba(139,92,246,0.40)',

        /* 功能色 */
        'success':       '#34d399',
        'warning':       '#fbbf24',
        'danger':        '#f87171',
        'info':          '#60a5fa',

        /* 边框 */
        'border-subtle': 'rgba(255,255,255,0.07)',
      },

      /* ── 圆角 ─────────────────────────────────────────── */
      borderRadius: {
        sm:  '6px',
        md:  '10px',
        lg:  '14px',
        xl:  '20px',
        xxl: '28px',
      },

      /* ── 阴影 ─────────────────────────────────────────── */
      boxShadow: {
        'sm':    '0 1px 3px rgba(0,0,0,0.40)',
        'md':    '0 4px 12px rgba(0,0,0,0.50)',
        'lg':    '0 8px 32px rgba(0,0,0,0.60)',
        'glow':  '0 0 20px rgba(139,92,246,0.25)',
      },
    },
  },
  plugins: [],
};
