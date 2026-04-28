import StatsDashboard from '../components/StatsDashboard'

export default function Dashboard() {
  return (
    <div className="space-y-5">
      {/* 品牌欢迎区 — 深紫主题卡片 */}
      <div className="card p-5 flex items-center gap-4 card-hover">
        {/* 品牌图标 */}
        <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0" style={{ background: 'rgba(139,92,246,0.15)' }}>
          <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="rgba(139,92,246,0.25)" />
            <circle cx="16" cy="16" r="7" fill="rgba(139,92,246,0.4)" />
            <circle cx="16" cy="16" r="3.5" fill="#8b5cf6" />
          </svg>
        </div>
        <div className="flex-1">
          <h1 className="text-text-primary font-medium text-[15px] tracking-tight">
            欢迎回来，张竹
          </h1>
          <p className="text-text-secondary text-[13px] mt-0.5">
            Cerealia Caviar · 高端鲟鱼子酱 B2B 客户关系管理
          </p>
        </div>
        <div className="hidden md:flex items-center gap-6 text-right">
          <div>
            <p className="text-[11px] text-text-muted uppercase tracking-widest">客户总数</p>
            <p className="text-text-primary text-[18px] font-light tabular-nums tracking-tight">—</p>
          </div>
          <div className="w-px h-8 border border-border-subtle" />
          <div>
            <p className="text-[11px] text-text-muted uppercase tracking-widest">本月邮件</p>
            <p className="text-text-primary text-[18px] font-light tabular-nums tracking-tight">—</p>
          </div>
        </div>
      </div>

      <StatsDashboard />
    </div>
  )
}
