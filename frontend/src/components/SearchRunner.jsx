import { useState, useEffect, useRef } from 'react'
import { runSearch, getSearchStatus } from '../api'

export default function SearchRunner({ product, keyword, countries, onReset }) {
  const [taskId, setTaskId] = useState(null)
  const [status, setStatus] = useState('idle')
  const [results, setResults] = useState([])
  const [current, setCurrent] = useState('')
  const [imported, setImported] = useState(0)
  const [error, setError] = useState('')
  const timer = useRef(null)

  useEffect(() => {
    async function run() {
      try {
        const r = await runSearch({ product_name: product, countries: countries.map(c => ({ code: c, name: c })), keyword })
        if (r?.data?.task_id) {
          setTaskId(r.data.task_id)
          setStatus('running')
        } else {
          setError('Failed to start search')
        }
      } catch (e) {
        setError(e.message)
      }
    }
    run()
  }, [])

  useEffect(() => {
    if (!taskId || status === 'completed' || status === 'failed') return

    timer.current = setInterval(async () => {
      try {
        const resp = await getSearchStatus(taskId)
        const d = resp?.data || resp
        if (d.status === 'completed') {
          setStatus('completed')
          setResults(d.results || [])
          setImported(d.imported_count || 0)
          clearInterval(timer.current)
        } else if (d.status === 'failed') {
          setStatus('failed')
          setError(d.error || 'Unknown error')
          clearInterval(timer.current)
        } else {
          setCurrent(d.current_country || '')
          setImported(d.partial_imported_count || d.imported_count || 0)
        }
      } catch (e) {
        setError(e.message)
        clearInterval(timer.current)
      }
    }, 3000)

    return () => clearInterval(timer.current)
  }, [taskId, status])

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* Status */}
      <div className="vercel-card" style={{ padding: '24px', marginBottom: 24 }}>
        <span className="vercel-mono">{status === 'completed' ? 'Complete' : status === 'failed' ? 'Failed' : 'Running'}</span>

        {status === 'running' && (
          <div style={{ marginTop: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#0a72ef', animation: 'pulse 1.5s infinite' }} />
              <span style={{ fontSize: 14, color: '#4d4d4d' }}>
                Searching {current || '...'}
              </span>
            </div>
            <span style={{ fontSize: 12, color: '#808080', marginLeft: 20 }}>{imported} imported</span>
          </div>
        )}

        {status === 'completed' && (
          <div style={{ marginTop: 8 }}>
            <p style={{ fontSize: 16, fontWeight: 600, color: '#171717' }}>
              {results.length} companies found · {imported} imported
            </p>
          </div>
        )}

        {error && (
          <p style={{ marginTop: 8, fontSize: 14, color: '#ff5b4f' }}>{error}</p>
        )}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="vercel-card" style={{ overflow: 'hidden' }}>
          <table className="vercel-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Country</th>
                <th>Website</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500, color: '#171717' }}>{r.company_name_en}</td>
                  <td style={{ color: '#4d4d4d' }}>{r.country}</td>
                  <td>
                    {r.website ? (
                      <a href={r.website} target="_blank" rel="noreferrer" style={{ fontSize: 13, color: '#0072f5' }}>
                        {r.website.replace('https://','').replace('www.','').slice(0,40)}
                      </a>
                    ) : (
                      <span style={{ color: '#808080' }}>—</span>
                    )}
                  </td>
                  <td>
                    <span className="vercel-pill">
                      {r.source === 'web_search' ? 'web' : 'ai'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        <button className="vercel-btn-ghost" onClick={onReset}>← New Search</button>
        {imported > 0 && (
          <button className="vercel-btn-dark" onClick={() => window.location.href = '/customers'}>
            View {imported} customers
          </button>
        )}
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
    </div>
  )
}
