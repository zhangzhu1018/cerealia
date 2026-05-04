import { useState, useEffect } from 'react'
import { getCustomers, generateEmail, sendEmailNow } from '../api'

export default function EmailPage() {
  const [customers, setCustomers] = useState([])
  const [selected, setSelected] = useState({})
  const [previews, setPreviews] = useState({})
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState({})

  useEffect(() => {
    getCustomers({ page: 1, pageSize: 50 }).then(r => {
      if (r?.data) setCustomers(r.data.items || [])
    }).catch(() => {})
  }, [])

  async function preview(id) {
    setLoading(true)
    try {
      const r = await generateEmail({ customer_id: id })
      setPreviews(p => ({ ...p, [id]: r?.data || r }))
    } catch (e) { alert(e.message) }
    setLoading(false)
  }

  async function send(id) {
    setLoading(true)
    try {
      await sendEmailNow({ customer_id: id, body: previews[id]?.body })
      setSent(s => ({ ...s, [id]: true }))
    } catch (e) { alert(e.message) }
    setLoading(false)
  }

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 300, color: '#061b31', letterSpacing: '-0.22px', margin: '0 0 4px' }}>
            Email Outreach
          </h1>
          <p style={{ fontSize: 14, fontWeight: 300, color: '#64748d' }}>
            AI-generated bilingual emails for customer outreach.
          </p>
        </div>
      </div>

      {customers.length === 0 ? (
        <div className="stripe-card" style={{ padding: 60, textAlign: 'center' }}>
          <p style={{ fontWeight: 300, color: '#64748d' }}>No customers yet. Search for caviar importers first.</p>
        </div>
      ) : (
        <div className="stripe-card" style={{ overflow: 'hidden' }}>
          <table className="stripe-table">
            <thead><tr><th>Company</th><th>Country</th><th>Website</th><th>Action</th></tr></thead>
            <tbody>
              {customers.filter(c => c.website).slice(0, 20).map(c => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 400, color: '#061b31' }}>{c.company_name_en}</td>
                  <td style={{ color: '#64748d' }}>{c.country}</td>
                  <td style={{ fontSize: 13, color: '#533afd' }}>
                    {c.website?.replace('https://','').replace('www.','').slice(0, 30)}
                  </td>
                  <td>
                    {sent[c.id] ? (
                      <span className="stripe-pill stripe-pill--green">Sent ✓</span>
                    ) : previews[c.id] ? (
                      <button className="stripe-btn" onClick={() => send(c.id)} disabled={loading}
                        style={{ fontSize: 13, padding: '5px 14px' }}>
                        Send Now
                      </button>
                    ) : (
                      <button className="stripe-btn-ghost" onClick={() => preview(c.id)} disabled={loading}
                        style={{ fontSize: 13, padding: '5px 14px' }}>
                        Generate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
