import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { previewImport, importCustomers } from '../api'

const FIELD_LABELS = {
  company_name_en: '公司英文名 *',
  company_name_local: '公司本地名',
  country: '国家 *',
  city: '城市',
  website: '网站',
  email: '邮箱',
  phone: '电话',
  customer_type: '客户类型',
  founded_year: '成立年份',
  employee_count: '员工数量',
  annual_revenue: '年收入',
  has_import_history: '有进口历史',
  import_frequency: '进口频率',
  typical_import_volume: '典型进口量',
  current_suppliers: '当前供应商',
  has_cites_license: 'CITES认证',
  has_haccp_cert: 'HACCP认证',
  market_segment: '市场细分',
  notes: '备注',
}

const STATUS_COLORS = {
  imported: 'text-green-400',
  skipped: 'text-yellow-400',
  failed: 'text-red-400',
}

const GRADE_COLORS = {
  A: 'text-green-400',
  B: 'text-lime-400',
  C: 'text-yellow-400',
  D: 'text-orange-400',
  E: 'text-red-400',
  N: 'text-caviar-muted',
}

export default function CustomerImportPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [step, setStep] = useState('upload') // upload | preview | importing | result
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState('')
  const [options, setOptions] = useState({
    runBackgroundCheck: true,
    skipDuplicates: true,
  })
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState(null)

  // ── 拖放处理 ─────────────────────────────────────────────────────────────
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [])

  const handleFileChange = (e) => {
    const f = e.target.files[0]
    if (f) handleFile(f)
  }

  const handleFile = async (f) => {
    const ext = f.name.toLowerCase().split('.').pop()
    if (!['xlsx', 'xls', 'csv'].includes(ext)) {
      setPreviewError('仅支持 .xlsx / .xls / .csv 文件')
      return
    }
    setFile(f)
    setPreviewError('')
    setPreviewLoading(true)

    try {
      const res = await previewImport(f)
      setPreview(res.data)
      setStep('preview')
    } catch (err) {
      setPreviewError(err.message || '预览失败')
    } finally {
      setPreviewLoading(false)
    }
  }

  // ── 开始导入 ─────────────────────────────────────────────────────────────
  const handleImport = async () => {
    setStep('importing')
    setImporting(true)
    try {
      const res = await importCustomers(file, options)
      setImportResult(res.data)
      setStep('result')
    } catch (err) {
      setPreviewError(err.message || '导入失败')
      setStep('preview')
    } finally {
      setImporting(false)
    }
  }

  // ── 重置 ─────────────────────────────────────────────────────────────────
  const handleReset = () => {
    setStep('upload')
    setFile(null)
    setPreview(null)
    setPreviewError('')
    setImportResult(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // ── 统计卡片 ─────────────────────────────────────────────────────────────
  const StatCard = ({ label, value, color = 'text-caviar-cream' }) => (
    <div className="bg-caviar-deep/60 border border-caviar-sienna/30 rounded-xl px-5 py-4 text-center">
      <div className={`text-3xl font-display font-bold ${color}`}>{value ?? '—'}</div>
      <div className="text-caviar-muted text-xs mt-1">{label}</div>
    </div>
  )

  return (
    <div className="space-y-6">

      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-display text-caviar-cream">📥 客户批量导入</h2>
          <p className="text-caviar-muted text-sm mt-1">
            上传 Excel / CSV 文件，自动识别字段并批量导入客户数据
          </p>
        </div>
        <button
          onClick={() => navigate('/customers')}
          className="text-sm text-caviar-muted hover:text-caviar-cream transition-colors"
        >
          ← 返回客户管理
        </button>
      </div>

      {/* ── 步骤指示器 ───────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        {['上传文件', '预览确认', '导入结果'].map((label, i) => {
          const stepIndex = ['upload', 'preview', 'result'].indexOf(step)
          const isActive = i <= stepIndex
          const isCurrent = i === stepIndex
          return (
            <div key={label} className="flex items-center gap-2">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border
                ${isCurrent ? 'bg-caviar-gold/20 border-caviar-gold text-caviar-gold'
                  : isActive ? 'bg-caviar-sienna/20 border-caviar-sienna/50 text-caviar-cream'
                  : 'border-caviar-sienna/20 text-caviar-muted'}`}>
                <span className="w-5 h-5 rounded-full bg-current/20 flex items-center justify-center text-[10px] font-bold">
                  {i + 1}
                </span>
                {label}
              </div>
              {i < 2 && <div className="w-8 h-px bg-caviar-sienna/30" />}
            </div>
          )
        })}
      </div>

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* 步骤1：文件上传 */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {step === 'upload' && (
        <div className="max-w-xl mx-auto">

          {/* 文件格式说明 */}
          <div className="card mb-4">
            <h3 className="text-caviar-cream font-medium text-sm mb-3">支持的文件格式</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { ext: '.xlsx / .xls', desc: 'Excel 文件，建议使用 .xlsx 格式', icon: '📊' },
                { ext: '.csv', desc: '逗号分隔值，UTF-8 编码', icon: '📄' },
              ].map(f => (
                <div key={f.ext} className="flex gap-3 p-3 bg-caviar-deep/50 rounded-lg">
                  <span className="text-2xl">{f.icon}</span>
                  <div>
                    <div className="text-caviar-gold text-sm font-medium">{f.ext}</div>
                    <div className="text-caviar-muted text-xs mt-0.5">{f.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 必填字段说明 */}
          <div className="card mb-4">
            <h3 className="text-caviar-cream font-medium text-sm mb-3">必填字段（系统自动识别）</h3>
            <div className="flex flex-wrap gap-2">
              {['公司英文名', '国家'].map(f => (
                <span key={f} className="px-3 py-1 bg-caviar-deep/60 border border-caviar-sienna/30 rounded-full text-xs text-caviar-gold">
                  {f} *
                </span>
              ))}
              {['城市', '网站', '邮箱', '电话', '客户类型', '成立年份', '年收入', '员工数量', '进口历史', 'CITES/HACCP认证'].map(f => (
                <span key={f} className="px-3 py-1 bg-caviar-deep/60 border border-caviar-sienna/20 rounded-full text-xs text-caviar-muted">
                  {f}
                </span>
              ))}
            </div>
            <p className="text-caviar-muted text-xs mt-3">
              支持多语言列名（中文/英文/法文/德文/俄文等），系统会自动识别对应字段。
            </p>
          </div>

          {/* 拖放区 */}
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-caviar-sienna/40 hover:border-caviar-gold/60
              rounded-2xl p-12 text-center cursor-pointer transition-all duration-200
              hover:bg-caviar-sienna/5 group"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-caviar-sienna/10 flex items-center justify-center
              group-hover:bg-caviar-sienna/20 transition-colors">
              <span className="text-3xl">📂</span>
            </div>
            <p className="text-caviar-cream font-medium mb-1">拖放文件到此处，或点击选择文件</p>
            <p className="text-caviar-muted text-xs">支持 .xlsx .xls .csv，最大 50MB</p>
          </div>

          {previewError && (
            <div className="mt-4 p-3 bg-red-900/20 border border-red-700/30 rounded-lg text-red-400 text-sm">
              {previewError}
            </div>
          )}

          {previewLoading && (
            <div className="mt-6 flex items-center justify-center gap-3 text-caviar-muted">
              <div className="w-5 h-5 border-2 border-caviar-gold border-t-transparent rounded-full animate-spin" />
              <span className="text-sm">正在解析文件...</span>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* 步骤2：预览确认 */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {step === 'preview' && preview && (
        <div className="space-y-4">

          {/* 文件信息 */}
          <div className="card flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">📊</span>
              <div>
                <div className="text-caviar-cream font-medium text-sm">{file?.name}</div>
                <div className="text-caviar-muted text-xs">
                  共 {preview.total_rows} 行数据 · {preview.headers.length} 列
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={handleReset} className="btn-secondary text-xs px-3 py-1.5">
                重新选择
              </button>
              <button
                onClick={async () => {
                  setPreviewLoading(true)
                  setPreviewError('')
                  try {
                    const res = await previewImport(file)
                    setPreview(res.data)
                  } catch (err) {
                    setPreviewError(err.message)
                  } finally {
                    setPreviewLoading(false)
                  }
                }}
                className="text-xs text-caviar-muted hover:text-caviar-cream transition-colors px-2"
              >
                🔄 刷新预览
              </button>
            </div>
          </div>

          {/* 列映射预览 */}
          <div className="card">
            <h3 className="text-caviar-cream font-medium text-sm mb-4 flex items-center gap-2">
              🔍 自动识别的字段映射
              <span className="text-caviar-muted text-xs font-normal">
                （系统已识别字段可跳过，确认后点击「开始导入」）
              </span>
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-caviar-sienna/20">
                    <th className="text-left py-2 pr-4 text-caviar-muted font-medium">目标字段</th>
                    <th className="text-left py-2 pr-4 text-caviar-muted font-medium">识别的表头</th>
                    <th className="text-left py-2 text-caviar-muted font-medium">示例值（前3行）</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.column_preview.map((col) => (
                    <tr key={col.field} className="border-b border-caviar-sienna/10 hover:bg-caviar-sienna/5">
                      <td className="py-2.5 pr-4">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          col.detected
                            ? 'bg-green-900/30 text-green-400 border border-green-700/30'
                            : 'bg-caviar-deep/60 text-caviar-muted border border-caviar-sienna/20'
                        }`}>
                          {FIELD_LABELS[col.field] || col.field}
                        </span>
                      </td>
                      <td className="py-2.5 pr-4 text-caviar-cream">
                        {col.detected ? (
                          <code className="text-caviar-gold text-[11px] bg-caviar-deep/60 px-1.5 py-0.5 rounded">
                            {col.source_header}
                          </code>
                        ) : (
                          <span className="text-caviar-muted/50 italic">未检测到</span>
                        )}
                      </td>
                      <td className="py-2.5">
                        <div className="flex flex-wrap gap-1">
                          {col.sample_values.length > 0 ? (
                            col.sample_values.map((v, i) => (
                              <span key={i} className="text-caviar-muted bg-caviar-deep/60 px-1.5 py-0.5 rounded truncate max-w-[120px]">
                                {v}
                              </span>
                            ))
                          ) : (
                            <span className="text-caviar-muted/40 italic">—</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 未识别警告 */}
          {!preview.column_preview.some(c => c.field === 'company_name_en' && c.detected) && (
            <div className="p-4 bg-yellow-900/20 border border-yellow-700/30 rounded-xl">
              <p className="text-yellow-400 text-sm font-medium mb-1">⚠️ 未检测到「公司名称」列</p>
              <p className="text-caviar-muted text-xs">
                请确保文件包含公司名称列（支持：公司名、company name、company 等），否则无法导入。
              </p>
            </div>
          )}

          {/* 导入选项 */}
          <div className="card">
            <h3 className="text-caviar-cream font-medium text-sm mb-3">导入选项</h3>
            <div className="space-y-2">
              {[
                { key: 'runBackgroundCheck', label: '自动执行背景评分', desc: '根据公司数据计算 A-E 等级和综合评分' },
                { key: 'skipDuplicates', label: '跳过重复客户', desc: '基于「公司名 + 国家」去重，已存在的客户将被跳过' },
              ].map(opt => (
                <label key={opt.key} className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={options[opt.key]}
                    onChange={(e) => setOptions({ ...options, [opt.key]: e.target.checked })}
                    className="mt-0.5 w-4 h-4 rounded border-caviar-sienna/40 bg-caviar-deep text-caviar-gold
                      focus:ring-caviar-gold focus:ring-offset-0 cursor-pointer"
                  />
                  <div>
                    <div className="text-caviar-cream text-sm group-hover:text-caviar-gold transition-colors">
                      {opt.label}
                    </div>
                    <div className="text-caviar-muted text-xs">{opt.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 确认导入 */}
          <div className="flex items-center justify-between">
            <div className="text-caviar-muted text-xs">
              将从 {preview.total_rows} 行数据中导入客户
              {preview.column_preview.find(c => c.field === 'company_name_en')?.detected ? '' : '（需先确认公司名称列已识别）'}
            </div>
            <button
              onClick={handleImport}
              disabled={importing || !preview.column_preview.some(c => c.field === 'company_name_en' && c.detected)}
              className="btn-primary disabled:opacity-50"
            >
              {importing ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-caviar-ivory border-t-transparent rounded-full animate-spin" />
                  导入中，请勿关闭页面...
                </span>
              ) : (
                '▶ 开始导入'
              )}
            </button>
          </div>

          {previewError && (
            <div className="p-3 bg-red-900/20 border border-red-700/30 rounded-lg text-red-400 text-sm">
              {previewError}
            </div>
          )}

          {importing && (
            <div className="text-center py-4 text-caviar-muted text-sm animate-pulse">
              正在处理 {preview.total_rows} 行数据，请稍候...
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* 步骤3：导入结果 */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {step === 'result' && importResult && (
        <div className="space-y-5">

          {/* 总体统计 */}
          <div className="grid grid-cols-4 gap-3">
            <StatCard label="总行数" value={importResult.total} />
            <StatCard label="✓ 成功导入" value={importResult.imported} color="text-green-400" />
            <StatCard label="⊘ 跳过" value={importResult.skipped} color="text-yellow-400" />
            <StatCard label="✗ 失败" value={importResult.failed} color="text-red-400" />
          </div>

          {/* 等级分布 */}
          {importResult.grade_stats && Object.values(importResult.grade_stats).some(v => v > 0) && (
            <div className="card">
              <h3 className="text-caviar-cream font-medium text-sm mb-4">📊 评分等级分布</h3>
              <div className="flex gap-2">
                {Object.entries(importResult.grade_stats).map(([grade, count]) => (
                  <div key={grade} className="flex-1 text-center">
                    <div className={`text-xl font-display font-bold ${GRADE_COLORS[grade] || 'text-caviar-muted'}`}>
                      {count}
                    </div>
                    <div className={`text-xs px-2 py-1 rounded-full mt-1 ${
                      grade !== 'N'
                        ? `bg-${GRADE_COLORS[grade]?.replace('text-', '')}/10 border border-current/20 ${GRADE_COLORS[grade]}`
                        : 'bg-caviar-deep/60 text-caviar-muted'
                    }`}>
                      {grade === 'N' ? '未评分' : `等级 ${grade}`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 国家分布 */}
          {importResult.country_stats && Object.keys(importResult.country_stats).length > 0 && (
            <div className="card">
              <h3 className="text-caviar-cream font-medium text-sm mb-4">🌍 国家分布</h3>
              <div className="space-y-2">
                {Object.entries(importResult.country_stats)
                  .sort((a, b) => b[1] - a[1])
                  .map(([country, count]) => {
                    const pct = Math.round(count / importResult.total * 100)
                    return (
                      <div key={country} className="flex items-center gap-3">
                        <div className="w-20 text-caviar-muted text-xs truncate">{country}</div>
                        <div className="flex-1 h-2 bg-caviar-deep/60 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-caviar-gold/60 rounded-full transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <div className="w-16 text-right text-caviar-cream text-xs">{count} 家</div>
                      </div>
                    )
                  })}
              </div>
            </div>
          )}

          {/* 错误信息 */}
          {importResult.errors?.length > 0 && (
            <div className="card">
              <h3 className="text-caviar-cream font-medium text-sm mb-3">⚠️ 错误详情</h3>
              <div className="space-y-1.5">
                {importResult.errors.map((err, i) => (
                  <div key={i} className="text-red-400 text-xs bg-red-900/10 px-3 py-1.5 rounded">
                    {err}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 明细表格（仅显示前50条） */}
          {importResult.results?.length > 0 && (
            <div className="card p-0 overflow-hidden">
              <div className="p-4 border-b border-caviar-sienna/20">
                <h3 className="text-caviar-cream font-medium text-sm">📋 导入明细（显示前50条）</h3>
              </div>
              <div className="overflow-x-auto max-h-80">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-caviar-deep/90">
                    <tr className="border-b border-caviar-sienna/20">
                      {['行号', '公司名称', '国家', '状态', '等级', '评分'].map(h => (
                        <th key={h} className="text-left px-4 py-2.5 text-caviar-muted font-medium whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {importResult.results.slice(0, 50).map((row, i) => (
                      <tr key={i} className="border-b border-caviar-sienna/10 hover:bg-caviar-sienna/5">
                        <td className="px-4 py-2 text-caviar-muted">{row.row}</td>
                        <td className="px-4 py-2 text-caviar-cream max-w-[200px] truncate">{row.company_name_en}</td>
                        <td className="px-4 py-2 text-caviar-muted">{row.country || '—'}</td>
                        <td className="px-4 py-2">
                          <span className={`text-xs ${STATUS_COLORS[row.status] || 'text-caviar-muted'}`}>
                            {{ imported: '✓ 已导入', skipped: '⊘ 跳过', failed: '✗ 失败' }[row.status] || row.status}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          {row.grade ? (
                            <span className={`text-xs font-bold ${GRADE_COLORS[row.grade] || 'text-caviar-muted'}`}>
                              {row.grade}
                            </span>
                          ) : '—'}
                        </td>
                        <td className="px-4 py-2 text-caviar-muted">
                          {row.score != null ? row.score.toFixed(1) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {importResult.results.length > 50 && (
                  <div className="p-3 text-center text-caviar-muted text-xs">
                    还有 {importResult.results.length - 50} 条记录未显示
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex items-center justify-between">
            <div className="text-caviar-muted text-sm">
              导入完成，共处理 {importResult.total} 行
            </div>
            <div className="flex gap-3">
              <button onClick={handleReset} className="btn-secondary">
                继续导入
              </button>
              <button
                onClick={() => navigate('/customers')}
                className="btn-primary"
              >
                查看客户列表 →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
