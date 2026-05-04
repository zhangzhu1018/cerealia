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
    async function go() {
      try {
        const r = await runSearch({ product_name: product, countries: countries.map(c => ({ code: c, name: c })), keyword })
        if (r?.data?.task_id) { setTaskId(r.data.task_id); setStatus('running') }
        else setError('Failed to start')
      } catch (e) { setError(e.message) }
    }
    go()
  }, [])

  useEffect(() => {
    if (!taskId || status === 'completed') return
    timer.current = setInterval(async () => {
      try {
        const resp = await getSearchStatus(taskId)
        const d = resp?.data || resp
        if (d.status === 'completed') {
          setStatus('completed'); setResults(d.results || [])
          setImported(d.imported_count || 0); clearInterval(timer.current)
        } else {
          setCurrent(d.current_country || d.country || '')
          setImported(d.partial_imported_count || d.imported_count || 0)
        }
      } catch (e) { setError(e.message) }
    }, 3000)
    return () => clearInterval(timer.current)
  }, [taskId])

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* Status card */}
      <div className="stripe-card" style={{ padding: 28, marginBottom: 24 }}>
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 11, fontWeight: 500, color: '#64748d',
          textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12,
        }}>
          {status === 'completed' ? 'Complete' : status === 'failed' ? 'Failed' : 'In Progress'}
        </div>

        {status === 'running' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#533afd', animation: 'p 1.5s infinite' }} />
            <span style={{ fontSize: 14, fontWeight: 300, color: '#64748d' }}>
              {current || 'Initializing...'}
            </span>
            <span style={{ fontSize: 13, fontWeight: 400, color: '#15be53', marginLeft: 8 }}>
              {imported} imported
            </span>
          </div>
        )}
        {status === 'completed' && (
          <div>
            <span style={{ fontSize: 28, fontWeight: 300, color: '#061b31', letterSpacing: '-0.03em' }}>
              {results.length}
            </span>
            <span style={{ fontSize: 14, fontWeight: 300, color: '#64748d', marginLeft: 8 }}>companies found</span>
            <span style={{ fontSize: 13, fontWeight: 400, color: '#15be53', marginLeft: 16 }}>{imported} imported</span>
          </div>
        )}
        {error && <p style={{ marginTop: 8, color: '#ea2261', fontSize: 14, fontWeight: 300 }}>{error}</p>}
      </div>

      {/* Results table */}
      {results.length > 0 && (
        <div className="stripe-card" style={{ overflow: 'hidden' }}>
          <table className="stripe-table">
            <thead><tr><th>Company</th><th>Country</th><th>Website</th><th>Source</th></tr></thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 400, color: '#061b31' }}>{r.company_name_en}</td>
                  <td style={{ color: '#64748d' }}>{r.country}</td>
                  <td>
                    {r.website ? (
                      <a href={r.website} target="_blank" rel="noreferrer" style={{ fontSize: 13, color: '#533afd', fontWeight: 400 }}>
                        {r.website.replace('https://','').replace('www.','').slice(0,35)}
                      </a>
                    ) : <span style={{ color: '#64748d' }}>—</span>}
                  </td>
                  <td>
                    <span className="stripe-pill stripe-pill--neutral">
                      {r.source === 'web_search' ? 'web' : 'ai'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
        <button className="stripe-btn-ghost" onClick={onReset}>← New Search</button>
        {imported > 0 && (
          <button className="stripe-btn" onClick={() => window.location.href = '/customers'}>
            View {imported} Customers
          </button>
        )}
      </div>
      <style>{`@keyframes p{0%,100%{opacity:1}50%{opacity:0.3}}`}</style>
    </div>
  )
}
