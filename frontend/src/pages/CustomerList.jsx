import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getCustomers } from '../api'

export default function CustomerList() {
  const [customers, setCustomers] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const PAGE_SIZE = 20

  useEffect(() => {
    getCustomers({ page, pageSize: PAGE_SIZE }).then(r => {
      if (r?.data) {
        setCustomers(r.data.items || [])
        setTotal(r.data.total || 0)
      }
    }).catch(() => {})
  }, [page])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.03em', color: '#171717', margin: 0 }}>
            Customers
          </h1>
          <p style={{ fontSize: 14, color: '#808080', marginTop: 4 }}>
            {total} verified caviar trade companies
          </p>
        </div>
        <Link to="/search" className="vercel-btn-dark" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          Search
        </Link>
      </div>

      <div className="vercel-card" style={{ overflow: 'hidden' }}>
        <table className="vercel-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Country</th>
              <th>Type</th>
              <th>Score</th>
              <th>Verified</th>
            </tr>
          </thead>
          <tbody>
            {customers.map(c => (
              <tr key={c.id}>
                <td>
                  <Link to={`/customers/${c.id}`} style={{ color: '#171717', fontWeight: 500, textDecoration: 'none' }}>
                    {c.company_name_en}
                  </Link>
                  {c.website && (
                    <a href={c.website} target="_blank" rel="noreferrer"
                      style={{ display: 'block', fontSize: 12, color: '#808080', marginTop: 2 }}>
                      {new URL(c.website).hostname}
                    </a>
                  )}
                </td>
                <td>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    {c.country?.name_cn || c.country}
                  </span>
                </td>
                <td>
                  {c.customer_type?.name_cn && (
                    <span className="vercel-pill">{c.customer_type.name_cn}</span>
                  )}
                </td>
                <td>
                  <span style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: c.background_score >= 60 ? '#171717' : '#808080',
                  }}>
                    {c.background_score ?? '—'}
                  </span>
                </td>
                <td>
                  {c.website_verified ? (
                    <span style={{ color: '#171717', fontSize: 13 }}>✓</span>
                  ) : (
                    <span style={{ color: '#808080', fontSize: 13 }}>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {customers.length === 0 && (
          <div style={{ padding: '80px 0', textAlign: 'center' }}>
            <span className="vercel-mono" style={{ display: 'block', marginBottom: 8 }}>No Customers</span>
            <p style={{ fontSize: 14, color: '#808080', marginBottom: 16 }}>
              Start by searching for caviar importers in your target countries.
            </p>
            <Link to="/search" className="vercel-btn-dark" style={{ textDecoration: 'none' }}>Start Search</Link>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 24 }}>
          <button className="vercel-btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
            ← Prev
          </button>
          <span style={{ fontSize: 13, color: '#808080', alignSelf: 'center', padding: '0 8px' }}>
            {page} / {totalPages}
          </span>
          <button className="vercel-btn-ghost" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
