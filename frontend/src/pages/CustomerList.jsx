import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getCustomers } from '../api'

export default function CustomerList() {
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const PS = 20

  useEffect(() => {
    getCustomers({ page, pageSize: PS }).then(r => {
      if (r?.data) { setItems(r.data.items || []); setTotal(r.data.total || 0) }
    }).catch(() => {})
  }, [page])

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 300, color: '#061b31', letterSpacing: '-0.22px', margin: '0 0 4px' }}>
            Customers
          </h1>
          <p style={{ fontSize: 14, fontWeight: 300, color: '#64748d' }}>
            {total} verified caviar trade companies
          </p>
        </div>
        <Link to="/search" className="stripe-btn" style={{ textDecoration: 'none' }}>
          New Search
        </Link>
      </div>

      <div className="stripe-card" style={{ overflow: 'hidden' }}>
        <table className="stripe-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Country</th>
              <th>Type</th>
              <th>Score</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map(c => (
              <tr key={c.id}>
                <td>
                  <Link to={`/customers/${c.id}`} style={{ color: '#061b31', fontWeight: 400, textDecoration: 'none' }}>
                    {c.company_name_en}
                  </Link>
                  {c.website && (
                    <span style={{ display: 'block', fontSize: 12, color: '#64748d', marginTop: 2 }}>
                      {new URL(c.website).hostname.replace('www.','')}
                    </span>
                  )}
                </td>
                <td style={{ fontSize: 13 }}>{c.country?.name_cn || c.country}</td>
                <td>
                  {c.customer_type?.name_cn && (
                    <span className="stripe-pill stripe-pill--purple">{c.customer_type.name_cn}</span>
                  )}
                </td>
                <td>
                  <span style={{
                    fontSize: 14, fontWeight: 400,
                    color: c.background_score >= 60 ? '#061b31' : '#64748d',
                  }}>
                    {c.background_score ?? '—'}
                  </span>
                </td>
                <td>
                  {c.website_verified ? (
                    <span className="stripe-pill stripe-pill--green">Verified</span>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {items.length === 0 && (
          <div style={{ padding: 80, textAlign: 'center' }}>
            <p style={{ fontWeight: 300, color: '#64748d', marginBottom: 16 }}>No customers yet</p>
            <Link to="/search" className="stripe-btn" style={{ textDecoration: 'none' }}>Start Search</Link>
          </div>
        )}
      </div>

      {Math.ceil(total / PS) > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 24 }}>
          <button className="stripe-btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
          <span style={{ fontSize: 13, color: '#64748d', fontWeight: 300, alignSelf: 'center', padding: '0 8px' }}>
            {page} / {Math.ceil(total / PS)}
          </span>
          <button className="stripe-btn-ghost" disabled={page * PS >= total} onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}
    </div>
  )
}
