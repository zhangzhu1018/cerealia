import { useState } from 'react'

// 评分徽章
const ScoreBadge = ({ score }) => {
  if (!score || score.total_score === undefined) return null
  const total = score.total_score
  const cls = total >= 75 ? 'text-emerald-400' : total >= 50 ? 'text-amber-400' : 'text-red-400'
  return (
    <span className={`font-mono font-bold text-sm ${cls}`} title="综合评分">
      {total}
    </span>
  )
}

// 评分维度小标签
const ScoreDims = ({ score }) => {
  if (!score) return null
  const dims = [
    { label: '进口', value: score.import_trade_score },
    { label: '规模', value: score.company_scale_score },
    { label: '资质', value: score.qualification_score },
    { label: '合作', value: score.cooperation_potential_score },
  ].filter(d => d.value !== undefined)
  return (
    <div className="flex gap-1.5 mt-1">
      {dims.map(d => (
        <span key={d.label} className="text-[10px] text-caviar-muted bg-caviar-dark/60 px-1.5 py-0.5 rounded">
          {d.label} {d.value}
        </span>
      ))}
    </div>
  )
}

// 搜索进度条（搜索中）
const SearchProgress = ({ seconds, currentCountry }) => {
  if (!seconds) return null
  return (
    <div className="card py-4">
      <div className="flex items-center justify-between mb-2 text-sm text-caviar-muted">
        <span className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-caviar-gold border-t-transparent rounded-full animate-spin" />
          {currentCountry ? (
            <>正在搜索：<strong className="text-caviar-gold">{currentCountry}</strong></>
          ) : (
            '正在搜索目标客户...'
          )}
        </span>
        <span>{seconds}s</span>
      </div>
      <div className="w-full bg-caviar-dark rounded-full h-1.5 overflow-hidden">
        <div
          className="h-full bg-caviar-gold rounded-full transition-all duration-1000 ease-linear"
          style={{ width: `${Math.min((seconds / 600) * 100, 100)}%` }}
        />
      </div>
      <p className="text-[11px] text-caviar-muted mt-1.5">
        全球多国家搜索预计需要 5-10 分钟，关闭页面后结果可在历史记录中查看
      </p>
    </div>
  )
}

// 国家搜索进度状态条（搜索结束后显示）
const CountryProgress = ({ searchProgress, onReset }) => {
  const { completed_countries = [], pending_countries = [] } = searchProgress
  const total = completed_countries.length + pending_countries.length
  if (total === 0) return null

  const pct = total > 0 ? (completed_countries.length / total) * 100 : 0
  const allDone = pending_countries.length === 0

  return (
    <div className="card py-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-caviar-muted">
          {allDone ? (
            <span className="text-emerald-400">✅ 全球搜索完毕</span>
          ) : (
            <>全球搜索进度 <span className="text-caviar-gold">{completed_countries.length}/{total}</span></>
          )}
        </span>
        {allDone && (
          <button
            onClick={onReset}
            className="text-[11px] text-caviar-muted hover:text-caviar-gold transition-colors underline"
          >
            重置进度，重新搜索
          </button>
        )}
      </div>

      {/* 国家进度条 */}
      <div className="w-full bg-caviar-dark rounded-full h-1.5 overflow-hidden mb-2">
        <div
          className={`h-full rounded-full transition-all duration-500 ${allDone ? 'bg-emerald-500' : 'bg-caviar-gold'}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* 国家标签 */}
      <div className="flex flex-wrap gap-1.5">
        {completed_countries.map(c => (
          <span key={c} className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-900/30 text-emerald-400 border border-emerald-700/30">
            ✅ {c}
          </span>
        ))}
        {pending_countries.map(c => (
          <span key={c} className="text-[10px] px-2 py-0.5 rounded-full bg-caviar-dark text-caviar-muted border border-caviar-sienna/20">
            ◯ {c}
          </span>
        ))}
      </div>

      {pending_countries.length > 0 && (
        <p className="text-[11px] text-caviar-muted mt-2">
          下次搜索将只搜索 <span className="text-caviar-gold">{pending_countries.join('、')}</span>，已搜国家自动跳过
        </p>
      )}
    </div>
  )
}

export default function SearchRunner({
  onRun, onAddCustomer, loading, progress, results, scores,
  scoringIdx, onScoreOne, addedIds,
  selectedItems, onSelectionChange, onBatchImport, batchImporting, batchImportResult,
  currentCountry,
  searchProgress,
  onResetProgress,
}) {
  const [keyword, setKeyword] = useState('')
  const [hsCode, setHsCode] = useState('')

  const handleRun = (e) => {
    e.preventDefault()
    if (!keyword.trim() && !hsCode.trim()) return
    onRun({ keyword: keyword.trim(), hs_code: hsCode.trim() })
  }

  const isAdded = (item) => {
    const name = item.company_name_en || item.company_name || ''
    return addedIds?.has(name)
  }

  const toggleItem = (item, idx) => {
    const key = item.company_name_en || item.company_name || `__idx_${idx}__`
    const next = new Set(selectedItems || [])
    if (next.has(key)) {
      next.delete(key)
    } else {
      next.add(key)
    }
    onSelectionChange && onSelectionChange(next)
  }

  const isSelected = (item, idx) => {
    const key = item.company_name_en || item.company_name || `__idx_${idx}__`
    return selectedItems?.has(key)
  }

  const allSelected = results && results.length > 0 && results.every((item, idx) => isAdded(item) || isSelected(item, idx))
  const someSelected = results && results.some((item, idx) => isSelected(item, idx) && !isAdded(item))

  const toggleAll = () => {
    const next = new Set(selectedItems || [])
    if (allSelected) {
      results.forEach((item, idx) => {
        if (!isAdded(item)) {
          const key = item.company_name_en || item.company_name || `__idx_${idx}__`
          next.delete(key)
        }
      })
    } else {
      results.forEach((item, idx) => {
        if (!isAdded(item)) {
          const key = item.company_name_en || item.company_name || `__idx_${idx}__`
          next.add(key)
        }
      })
    }
    onSelectionChange && onSelectionChange(next)
  }

  const selectedCount = results
    ? results.filter((item, idx) => isSelected(item, idx) && !isAdded(item)).length
    : 0

  // 所有国家搜完了
  const allDone = searchProgress?.pending_countries?.length === 0 &&
    (searchProgress?.completed_countries?.length || 0) > 0

  return (
    <div className="space-y-6">
      {/* 搜索表单 */}
      <form onSubmit={handleRun} className="card">
        <h3 className="text-caviar-cream font-display text-base mb-4">搜索目标客户</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-caviar-muted text-xs mb-1.5 uppercase tracking-wide">
              关键词
            </label>
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="input-field w-full"
              placeholder="例: caviar, 鲟鱼子酱"
            />
          </div>
          <div>
            <label className="block text-caviar-muted text-xs mb-1.5 uppercase tracking-wide">
              HS CODE <span className="normal-case font-normal opacity-60">（可选）</span>
            </label>
            <input
              value={hsCode}
              onChange={(e) => setHsCode(e.target.value)}
              className="input-field w-full"
              placeholder="例: 1604.31.00"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={loading || (!keyword.trim() && !hsCode.trim())}
              className="btn-primary w-full disabled:opacity-40"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-caviar-ivory border-t-transparent rounded-full animate-spin" />
                  搜索中...
                </span>
              ) : allDone ? (
                '🔄 继续搜索待搜国家'
              ) : (
                '🔍 开始搜索'
              )}
            </button>
          </div>
        </div>
      </form>

      {/* 国家搜索进度 */}
      <CountryProgress searchProgress={searchProgress || {}} onReset={onResetProgress} />

      {/* 搜索进度条（搜索中） */}
      <SearchProgress seconds={progress} currentCountry={currentCountry} />

      {/* 全部国家搜完了 */}
      {allDone && !loading && !results.length && (
        <div className="card text-center py-8">
          <p className="text-caviar-muted mb-2">所有国家已搜索完毕</p>
          <p className="text-xs text-caviar-muted">点击上方"继续搜索待搜国家"可重新搜索，或使用"重置进度"从头开始</p>
        </div>
      )}

      {/* 搜索结果 */}
      {results && results.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <h3 className="text-caviar-cream font-display text-base">
              搜索结果 ({results.length})
            </h3>

            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1.5 cursor-pointer text-xs text-caviar-muted hover:text-caviar-cream transition-colors select-none">
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={(el) => { if (el) el.indeterminate = someSelected && !allSelected }}
                  onChange={toggleAll}
                  className="w-3.5 h-3.5 rounded border-caviar-sienna/40 bg-caviar-dark accent-caviar-gold cursor-pointer"
                />
                全选
              </label>

              {selectedCount > 0 && (
                <button
                  onClick={onBatchImport}
                  disabled={batchImporting}
                  className="btn-primary text-sm flex items-center gap-1.5"
                >
                  {batchImporting ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-caviar-ivory border-t-transparent rounded-full animate-spin" />
                      导入中...
                    </>
                  ) : (
                    <>📥 导入客户池 ({selectedCount})</>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* 批量导入结果提示 */}
          {batchImportResult && (
            <div className={`mb-4 p-3 rounded-lg text-sm flex items-center justify-between ${
              batchImportResult.failed === 0
                ? 'bg-emerald-900/20 border border-emerald-700/30 text-emerald-400'
                : 'bg-amber-900/20 border border-amber-700/30 text-amber-400'
            }`}>
              <span>
                ✅ 成功导入 <strong>{batchImportResult.imported}</strong> 条
                {batchImportResult.skipped > 0 && ` · ⊘ 跳过 ${batchImportResult.skipped} 条（已在库中）`}
                {batchImportResult.failed > 0 && ` · ✗ 失败 ${batchImportResult.failed} 条`}
              </span>
              <button
                onClick={() => onBatchImport && onBatchImport(null, true)}
                className="text-xs underline hover:no-underline"
              >
                清除
              </button>
            </div>
          )}

          <div className="space-y-2">
            {results.map((item, idx) => {
              const score = scores?.[idx]
              const isScoringThis = scoringIdx === idx
              const itemAdded = isAdded(item)
              const itemSelected = isSelected(item, idx)

              return (
                <div
                  key={idx}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                    itemAdded
                      ? 'bg-emerald-900/10 border border-emerald-700/20 opacity-60'
                      : itemSelected
                        ? 'bg-caviar-gold/5 border border-caviar-gold/30'
                        : 'bg-caviar-dark/40 border border-caviar-sienna/15 hover:border-caviar-cream/20'
                  }`}
                >
                  {!itemAdded && (
                    <input
                      type="checkbox"
                      checked={itemSelected}
                      onChange={() => toggleItem(item, idx)}
                      className="w-3.5 h-3.5 flex-shrink-0 rounded border-caviar-sienna/40 bg-caviar-dark accent-caviar-gold cursor-pointer"
                    />
                  )}
                  {itemAdded && <div className="w-3.5 h-3.5 flex-shrink-0" />}

                  <div className="flex-shrink-0 w-14 text-center">
                    {itemAdded ? (
                      <span className="text-emerald-400 text-xs">✅ 已入库</span>
                    ) : isScoringThis ? (
                      <div className="w-8 h-8 mx-auto border-2 border-caviar-gold border-t-transparent rounded-full animate-spin" />
                    ) : score ? (
                      <ScoreBadge score={score} />
                    ) : (
                      <button
                        onClick={() => onScoreOne && onScoreOne(item, idx)}
                        className="text-caviar-muted hover:text-caviar-gold text-xs transition-colors"
                        title="点击评分"
                      >
                        ⭐ 评分
                      </button>
                    )}
                    {score && !itemAdded && <ScoreDims score={score} />}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-caviar-cream font-medium truncate">
                      {item.company_name_en || item.company_name}
                    </p>
                    {item.website && (
                      <p className="text-caviar-muted text-xs truncate mt-0.5">{item.website}</p>
                    )}
                    {item.snippet && (
                      <p className="text-caviar-muted text-xs mt-1 line-clamp-1">{item.snippet}</p>
                    )}
                    {item.country && (
                      <span className="inline-block mt-1 text-[10px] text-caviar-gold/70 bg-caviar-gold/10 px-1.5 py-0.5 rounded">
                        🌍 {item.country}
                      </span>
                    )}
                  </div>

                  {itemAdded ? (
                    <span className="text-emerald-400 text-xs py-1.5 px-3 flex-shrink-0">已添加</span>
                  ) : (
                    <button
                      onClick={() => onAddCustomer && onAddCustomer(item, idx)}
                      disabled={isScoringThis}
                      className="btn-secondary text-xs py-1.5 px-3 flex-shrink-0 disabled:opacity-40"
                    >
                      + 添加
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {results && results.length === 0 && !loading && !progress && (
        <div className="card text-center py-12 text-caviar-muted">
          请输入关键词开始搜索
        </div>
      )}
    </div>
  )
}
