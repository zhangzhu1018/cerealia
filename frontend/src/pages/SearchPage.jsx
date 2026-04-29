import { useState, useCallback, useEffect, useRef } from 'react'
import SearchRunner from '../components/SearchRunner'
import { runSearch, createCustomer, calculateScore, getCustomers, importSearchResults, resetSearchProgress } from '../api'

export default function SearchPage() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [scores, setScores] = useState({})   // { idx: score_result }
  const [scoringIdx, setScoringIdx] = useState(null)
  const [error, setError] = useState('')
  const [searchSeconds, setSearchSeconds] = useState(0)
  const [currentCountry, setCurrentCountry] = useState('')
  const [addedIds, setAddedIds] = useState(new Set())     // 已添加的客户名
  const [selectedItems, setSelectedItems] = useState(new Set())
  const [batchImporting, setBatchImporting] = useState(false)
  const [batchImportResult, setBatchImportResult] = useState(null)
  // 增量搜索状态：哪些国家已搜完，哪些待搜
  const [searchProgress, setSearchProgress] = useState({ completed_countries: [], pending_countries: [] })
  // 当前搜索关键词（用于重置时传递正确key）
  const [currentKeyword, setCurrentKeyword] = useState('')

  // ── 轮询控制 refs（避免闭包陷阱）──────────────────────────────────────────
  const pollingRef = useRef(null)   // { taskId, abortController, seconds, tick }

  // ── 轮询 effect：组件卸载时自动停止 ───────────────────────────────────────
  useEffect(() => {
    return () => {
      // 组件卸载时强制停止所有轮询
      if (pollingRef.current) {
        pollingRef.current._stopped = true
        pollingRef.current.abortController?.abort()
        if (pollingRef.current.tick) clearInterval(pollingRef.current.tick)
        pollingRef.current = null
      }
    }
  }, [])

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      pollingRef.current._stopped = true
      pollingRef.current.abortController?.abort()
      if (pollingRef.current.tick) clearInterval(pollingRef.current.tick)
      pollingRef.current = null
    }
    setSearchSeconds(0)
    setLoading(false)
  }, [])

  const handleSearch = useCallback(async (params) => {
    // ── 停掉上一个轮询 ─────────────────────────────────────────────────────
    stopPolling()

    setLoading(true)
    setError('')
    setResults([])
    setScores({})
    setAddedIds(new Set())
    setSelectedItems(new Set())
    setBatchImportResult(null)
    setCurrentCountry('')
    // 保存当前关键词（用于重置）
    const kw = params.keyword || params.product_name || ''
    setCurrentKeyword(kw)

    try {
      const res = await runSearch({
        product_name: params.keyword || params.product_name || '',
        hs_code: params.hs_code || '',
      })

      const taskData = res?.data || res

      // 所有国家都搜完了
      if (taskData?.status === 'all_completed') {
        setSearchProgress({
          completed_countries: taskData.completed_countries || [],
          pending_countries: [],
        })
        setLoading(false)
        return
      }

      const taskId = taskData?.task_id
      if (!taskId) {
        setError('搜索任务创建失败')
        return
      }

      // 更新前端显示的待搜国家
      if (taskData?.pending_countries) {
        setSearchProgress({
          completed_countries: taskData.completed_countries || [],
          pending_countries: taskData.pending_countries,
        })
      }

      // ── 初始化轮询状态 ───────────────────────────────────────────────────
      const abortController = new AbortController()
      let seconds = 0
      const tick = setInterval(() => {
        seconds += 1
        setSearchSeconds(seconds)
      }, 1000)

      pollingRef.current = { taskId, abortController, tick, _stopped: false }

      let data = []
      let pollingError = null

      // ── 轮询循环：最多 2 小时，React 卸载或 stopPolling 可中断 ─────────────
      try {
        for (let i = 0; i < 7200; i++) {
          // 检查是否已停止（React 卸载或用户取消）
          if (pollingRef.current?._stopped || abortController.signal.aborted) {
            pollingError = null   // 非错误，安静退出
            break
          }

          await new Promise((resolve, reject) => {
            const t = setTimeout(() => {
              // 再次检查停止标记（等待期间可能被 stop）
              if (pollingRef.current?._stopped || abortController.signal.aborted) {
                reject(new Error('CANCELLED'))
              } else {
                resolve()
              }
            }, 1000)
            abortController.signal.addEventListener('abort', () => {
              clearTimeout(t)
              reject(new Error('CANCELLED'))
            })
          })

          try {
            const statusRes = await fetch(`/api/search/status/${taskId}`, {
              signal: abortController.signal,
            })
            const statusData = await statusRes.json()
            const status = statusData?.data

            if (status?.current_country) {
              setCurrentCountry(status.current_country)
              setSearchProgress(prev => {
                const done = new Set(prev.completed_countries)
                done.add(status.current_country)
                const pending = prev.pending_countries.filter(c => c !== status.current_country)
                return { completed_countries: [...done], pending_countries: pending }
              })
            }
            if (status?.status === 'completed') {
              data = status.results || []
              break
            }
            if (status?.status === 'failed') {
              throw new Error(status.error || '搜索失败')
            }
            // 每 30 秒打印一次进度提示
            if (i > 0 && i % 30 === 0) {
              console.log(`[SearchPage] 进行中 ${i}s，已完成 ${status?.country_index || 0}/${status?.total_countries || '?'} 个国家`)
            }
          } catch (fetchErr) {
            if (fetchErr.message === 'CANCELLED') {
              pollingError = null
              break
            }
            throw fetchErr
          }
        }

        if (!data.length && !pollingError && !pollingRef.current?._stopped) {
          throw new Error(`搜索进行中（${seconds}秒），可关闭页面稍后从历史记录查看结果`)
        }
      } finally {
        // 清理：停止计时器，移除 pollingRef
        if (pollingRef.current?.taskId === taskId) {
          if (pollingRef.current.tick) clearInterval(pollingRef.current.tick)
          pollingRef.current = null
        }
        setSearchSeconds(0)
      }

      // 如果被停止（用户取消或组件卸载），不再更新结果
      if (!data.length) return

      setResults(data)

      // ── 自动导入全部结果到客户池（后台静默执行）────────────────────────────
      try {
        const importRes = await importSearchResults(data)
        const importResult = importRes?.data || importRes
        const importedNames = new Set(
          (importResult.results || [])
            .filter(r => r.status === 'imported')
            .map(r => r.company_name_en)
        )
        if (importedNames.size > 0) {
          setAddedIds(prev => new Set([...prev, ...importedNames]))
        }
        // 显示导入结果提示（不打断流程）
        if (importResult.imported > 0 || importResult.skipped > 0) {
          setBatchImportResult({
            imported: importResult.imported || 0,
            skipped: importResult.skipped || 0,
            failed: importResult.failed || 0,
          })
        }
      } catch (_) {
        // 导入失败不影响评分，继续执行
      }

      // 前 5 条自动评分
      const quickBatch = data.slice(0, 5).map((item, idx) => ({
        idx,
        data: {
          company_name_en: item.company_name_en || item.company_name || '',
          description: item.snippet || item.description || '',
          website: item.website || '',
          country: item.country || '',
        }
      }))
      for (const { idx, data: companyData } of quickBatch) {
        try {
          const scoreRes = await calculateScore({ company_data: companyData })
          const score = scoreRes?.data || scoreRes
          if (score && score.total_score !== undefined) {
            setScores(prev => ({ ...prev, [idx]: score }))
          }
        } catch (_) {}
      }
    } catch (err) {
      setError(err.message || '搜索失败，请重试')
    } finally {
      setLoading(false)
    }
  }, [])

  const handleScoreOne = useCallback(async (item, idx) => {
    setScoringIdx(idx)
    try {
      const scoreRes = await calculateScore({
        company_data: {
          company_name_en: item.company_name_en || item.company_name || '',
          description: item.snippet || item.description || '',
          website: item.website || '',
          country: item.country || '',
        }
      })
      const score = scoreRes?.data || scoreRes
      if (score && score.total_score !== undefined) {
        setScores(prev => ({ ...prev, [idx]: score }))
      }
    } catch (_) {
    } finally {
      setScoringIdx(null)
    }
  }, [])

  const handleAddCustomer = useCallback(async (item, idx) => {
    const name = item.company_name_en || item.company_name || ''
    if (!name) {
      alert('公司名称为空，无法添加')
      return
    }
    if (addedIds.has(name)) {
      alert(`⚠️ "${name}" 已添加，无需重复操作`)
      return
    }

    try {
      const res = await getCustomers({ page_size: 200, keyword: name })
      const list = res?.data?.items || []
      const isDuplicate = list.some(
        c => c.company_name_en?.toLowerCase() === name.toLowerCase()
          || c.company_name_local?.toLowerCase() === name.toLowerCase()
      )
      if (isDuplicate) {
        alert(`⚠️ "${name}" 已在客户库中，跳过添加`)
        setAddedIds(prev => new Set([...prev, name]))
        return
      }
    } catch (_) {}

    let scoreData = scores[idx]
    if (!scoreData) {
      setScoringIdx(idx)
      try {
        const scoreRes = await calculateScore({
          company_data: {
            company_name_en: name,
            description: item.snippet || item.description || '',
            website: item.website || '',
            country: item.country || '',
          }
        })
        scoreData = scoreRes?.data || scoreRes
        if (scoreData && scoreData.total_score !== undefined) {
          setScores(prev => ({ ...prev, [idx]: scoreData }))
        }
      } catch (_) {}
      setScoringIdx(null)
    }

    try {
      await createCustomer({
        company_name_en: name,
        website: item.website || '',
        country_name: item.country || '',
        notes: `来源：客户搜索\n描述：${item.snippet || item.description || ''}\n评分：${scoreData?.total_score ?? '待评分'}`,
        search_source: 'customer_search',
        is_collected: true,
      })
      setAddedIds(prev => new Set([...prev, name]))
      const key = item.company_name_en || item.company_name || `__idx_${idx}__`
      setSelectedItems(prev => {
        const next = new Set(prev)
        next.delete(key)
        return next
      })
      alert(`✅ 已添加：${name}`)
    } catch (err) {
      alert('添加失败: ' + err.message)
    }
  }, [addedIds, scores])

  const handleBatchImport = useCallback(async (_, clearFlag) => {
    if (clearFlag) {
      setBatchImportResult(null)
      return
    }

    const itemsToImport = results
      .map((item, idx) => ({ item, idx }))
      .filter(({ item, idx }) => {
        const key = item.company_name_en || item.company_name || `__idx_${idx}__`
        return selectedItems.has(key) && !addedIds.has(item.company_name_en || item.company_name || '')
      })
      .map(({ item }) => item)

    if (itemsToImport.length === 0) {
      alert('请先选择要导入的客户')
      return
    }

    if (!window.confirm(`确定要导入 ${itemsToImport.length} 家客户到客户池吗？\n已在库中的客户会被自动跳过。`)) {
      return
    }

    setBatchImporting(true)
    try {
      const res = await importSearchResults(itemsToImport)
      const result = res?.data || res

      const importedNames = new Set(
        (result.results || [])
          .filter(r => r.status === 'imported')
          .map(r => r.company_name_en)
      )
      if (importedNames.size > 0) {
        setAddedIds(prev => new Set([...prev, ...importedNames]))
        setSelectedItems(new Set())
      }

      setBatchImportResult({
        imported: result.imported || 0,
        skipped: result.skipped || 0,
        failed: result.failed || 0,
      })

      if (result.imported === 0 && result.skipped > 0) {
        alert(`⚠️ 全部 ${result.skipped} 条已在客户库中，无需重复导入`)
      } else {
        alert(`✅ 成功导入 ${result.imported} 条客户${result.skipped > 0 ? `，跳过 ${result.skipped} 条（已在库）` : ''}${result.failed > 0 ? `，失败 ${result.failed} 条` : ''}`)
      }
    } catch (err) {
      alert('批量导入失败: ' + err.message)
    } finally {
      setBatchImporting(false)
    }
  }, [results, selectedItems, addedIds])

  const handleResetProgress = useCallback(async () => {
    if (!window.confirm('确定要重置搜索进度吗？这将清除已搜国家记录，下次搜索会从头开始。')) return
    try {
      // 用当前关键词的key重置，确保能正确删除记录
      await resetSearchProgress({ product_name: currentKeyword, hs_code: '' })
      setSearchProgress({ completed_countries: [], pending_countries: [] })
      alert('✅ 进度已重置，下次搜索将从头开始')
    } catch (err) {
      // 即使后端报错，前端状态也清空，用户体验优先
      setSearchProgress({ completed_countries: [], pending_countries: [] })
      alert('⚠️ 重置完成（' + (err.message || '') + '）')
    }
  }, [currentKeyword])

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 bg-red-900/20 border border-red-700/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      <SearchRunner
        onRun={handleSearch}
        onStop={stopPolling}
        onAddCustomer={handleAddCustomer}
        loading={loading}
        progress={searchSeconds}
        results={results}
        scores={scores}
        scoringIdx={scoringIdx}
        onScoreOne={handleScoreOne}
        addedIds={addedIds}
        selectedItems={selectedItems}
        onSelectionChange={setSelectedItems}
        onBatchImport={handleBatchImport}
        batchImporting={batchImporting}
        batchImportResult={batchImportResult}
        currentCountry={currentCountry}
        searchProgress={searchProgress}
        onResetProgress={handleResetProgress}
      />
    </div>
  )
}
