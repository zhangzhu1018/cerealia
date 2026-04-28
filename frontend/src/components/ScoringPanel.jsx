import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, Tooltip,
} from 'recharts'

const dimensions = [
  { key: 'company_scale', label: '公司规模' },
  { key: 'market_position', label: '市场地位' },
  { key: 'financial_health', label: '财务健康' },
  { key: 'import_potential', label: '进口潜力' },
  { key: 'certification', label: '资质认证' },
  { key: 'reputation', label: '行业声誉' },
  { key: 'growth_potential', label: '增长潜力' },
]

export default function ScoringPanel({ scoreResult }) {
  if (!scoreResult) {
    return (
      <div className="card flex items-center justify-center h-64 text-caviar-muted">
        暂无评分数据
      </div>
    )
  }

  const { scores, total_score, grade } = scoreResult
  const radarData = dimensions.map((d) => ({
    dimension: d.label,
    score: scores?.[d.key] || 0,
    fullMark: 100,
  }))

  const gradeColor = {
    A: 'text-emerald-400',
    B: 'text-blue-400',
    C: 'text-amber-400',
    D: 'text-red-400',
  }[grade] || 'text-caviar-muted'

  return (
    <div className="space-y-6">
      {/* 总分 + 等级 */}
      <div className="flex items-center gap-6">
        <div className="card flex-1 text-center">
          <p className="text-caviar-muted text-xs uppercase tracking-wide mb-1">综合评分</p>
          <p className="text-4xl font-bold font-display text-caviar-cream">{total_score}</p>
          <p className="text-caviar-muted text-xs mt-1">/ 100</p>
        </div>
        <div className="card flex-1 text-center">
          <p className="text-caviar-muted text-xs uppercase tracking-wide mb-1">客户等级</p>
          <p className={`text-4xl font-bold font-display ${gradeColor}`}>{grade}</p>
          <p className="text-caviar-muted text-xs mt-1">
            {grade === 'A' && '顶级客户'}
            {grade === 'B' && '优质客户'}
            {grade === 'C' && '潜力客户'}
            {grade === 'D' && '观望客户'}
          </p>
        </div>
      </div>

      {/* 雷达图 */}
      <div className="card">
        <h3 className="text-caviar-cream font-display text-base mb-4">七维度评分</h3>
        <ResponsiveContainer width="100%" height={350}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#8B4513" strokeDasharray="3 3" />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fill: '#D4A574', fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: '#9A8B7F', fontSize: 10 }}
              axisLine={false}
            />
            <Radar
              name="评分"
              dataKey="score"
              stroke="#C9A96E"
              fill="#C9A96E"
              fillOpacity={0.2}
              strokeWidth={2}
            />
            <Tooltip
              contentStyle={{
                background: '#3D1F0A',
                border: '1px solid #D4A574',
                borderRadius: '8px',
                color: '#F5F0EB',
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* 分数条形图 */}
      <div className="card space-y-3">
        {dimensions.map((d) => {
          const val = scores?.[d.key] || 0
          const color =
            val >= 80 ? 'bg-emerald-500' :
            val >= 60 ? 'bg-blue-500' :
            val >= 40 ? 'bg-amber-500' : 'bg-red-500'
          return (
            <div key={d.key} className="flex items-center gap-3">
              <span className="text-caviar-text text-sm w-20 text-right">{d.label}</span>
              <div className="flex-1 h-2 bg-caviar-dark/60 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${color} transition-all duration-500`}
                  style={{ width: `${val}%` }}
                />
              </div>
              <span className="text-caviar-cream text-sm font-medium w-10 text-right">{val}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
