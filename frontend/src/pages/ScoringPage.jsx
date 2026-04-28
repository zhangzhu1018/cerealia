import { useState } from 'react'
import ScoringPanel from '../components/ScoringPanel'
import { calculateScore } from '../api'

const customerTypes = ['进口商', '批发商', '品牌商', '米其林餐厅', '高端酒店', '零售商', '其他']

export default function ScoringPage() {
  const [form, setForm] = useState({
    company_name: '',
    year_established: '',
    employee_count: '',
    annual_revenue: '',
    import_history: 'no',
    certifications: '',
    country: '',
    customer_type: '',
    website: '',
    industry_years: '',
    online_presence: 'medium',
    michelin_recognized: 'no',
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const payload = {
        ...form,
        year_established: form.year_established ? parseInt(form.year_established) : null,
        employee_count: form.employee_count ? parseInt(form.employee_count) : null,
        annual_revenue: form.annual_revenue ? parseFloat(form.annual_revenue) : null,
        industry_years: form.industry_years ? parseInt(form.industry_years) : null,
      }
      const res = await calculateScore(payload)
      setResult(res)
    } catch (err) {
      setError(err.message || '评分失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 评分表单 */}
      <div className="card">
        <h3 className="text-caviar-cream font-display text-base mb-4">背调评分工具</h3>
        <p className="text-caviar-muted text-sm mb-6">
          输入客户信息，系统将从7个维度自动评估客户质量与合作潜力。
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 基本信息 */}
          <div className="space-y-3">
            <h4 className="text-caviar-cream text-sm font-medium border-b border-caviar-sienna/20 pb-2">
              基本信息
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-caviar-muted text-xs mb-1">公司名称 *</label>
                <input name="company_name" value={form.company_name} onChange={handleChange}
                  required className="input-field w-full text-sm" placeholder="公司全称" />
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">国家 *</label>
                <input name="country" value={form.country} onChange={handleChange}
                  required className="input-field w-full text-sm" placeholder="France" />
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">客户类型</label>
                <select name="customer_type" value={form.customer_type} onChange={handleChange}
                  className="select-field w-full text-sm">
                  <option value="">选择类型</option>
                  {customerTypes.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">网站</label>
                <input name="website" value={form.website} onChange={handleChange}
                  className="input-field w-full text-sm" placeholder="https://..." />
              </div>
            </div>
          </div>

          {/* 规模信息 */}
          <div className="space-y-3">
            <h4 className="text-caviar-cream text-sm font-medium border-b border-caviar-sienna/20 pb-2">
              规模与财务
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-caviar-muted text-xs mb-1">成立年份</label>
                <input name="year_established" type="number" value={form.year_established}
                  onChange={handleChange} className="input-field w-full text-sm" placeholder="1990" />
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">员工数</label>
                <input name="employee_count" type="number" value={form.employee_count}
                  onChange={handleChange} className="input-field w-full text-sm" placeholder="50" />
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">年营收 (万美元)</label>
                <input name="annual_revenue" type="number" value={form.annual_revenue}
                  onChange={handleChange} className="input-field w-full text-sm" placeholder="500" />
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">行业年限</label>
                <input name="industry_years" type="number" value={form.industry_years}
                  onChange={handleChange} className="input-field w-full text-sm" placeholder="15" />
              </div>
            </div>
          </div>

          {/* 资质信息 */}
          <div className="space-y-3">
            <h4 className="text-caviar-cream text-sm font-medium border-b border-caviar-sienna/20 pb-2">
              资质与声誉
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-caviar-muted text-xs mb-1">进口历史</label>
                <select name="import_history" value={form.import_history} onChange={handleChange}
                  className="select-field w-full text-sm">
                  <option value="no">无进口经验</option>
                  <option value="other">进口其他食品</option>
                  <option value="similar">进口类似产品</option>
                  <option value="direct">直接进口鱼子酱</option>
                </select>
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">米其林认证</label>
                <select name="michelin_recognized" value={form.michelin_recognized}
                  onChange={handleChange} className="select-field w-full text-sm">
                  <option value="no">否</option>
                  <option value="star">米其林星级</option>
                  <option value="recommended">米其林推荐</option>
                </select>
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">线上影响力</label>
                <select name="online_presence" value={form.online_presence} onChange={handleChange}
                  className="select-field w-full text-sm">
                  <option value="low">低（无官网/社交媒体）</option>
                  <option value="medium">中（有官网）</option>
                  <option value="high">高（官网+社交媒体活跃）</option>
                </select>
              </div>
              <div>
                <label className="block text-caviar-muted text-xs mb-1">认证信息</label>
                <input name="certifications" value={form.certifications} onChange={handleChange}
                  className="input-field w-full text-sm" placeholder="HACCP, ISO, Organic..." />
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-900/20 border border-red-700/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-50">
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-caviar-ivory border-t-transparent rounded-full animate-spin" />
                评估中...
              </span>
            ) : (
              '⭐ 开始评分'
            )}
          </button>
        </form>
      </div>

      {/* 评分结果 */}
      <div>
        <ScoringPanel scoreResult={result} />
      </div>
    </div>
  )
}
