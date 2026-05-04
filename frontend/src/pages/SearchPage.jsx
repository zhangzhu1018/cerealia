import { useState } from 'react'
import SearchRunner from '../components/SearchRunner'

const TIER1 = ['France','USA','Italy','Germany','Spain','Japan','UK','Switzerland','UAE','Netherlands','Belgium','Australia','Canada','Singapore','Hong Kong']

export default function SearchPage() {
  const [product, setProduct] = useState('caviar')
  const [keyword, setKeyword] = useState('')
  const [selected, setSelected] = useState(['France','Spain','Italy','Germany','Japan'])
  const [started, setStarted] = useState(false)

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <h1 style={{ fontSize: 22, fontWeight: 300, color: '#061b31', letterSpacing: '-0.22px', margin: '0 0 4px' }}>
        Customer Search
      </h1>
      <p style={{ fontSize: 14, fontWeight: 300, color: '#64748d', marginBottom: 24 }}>
        AI-powered discovery for premium caviar trade partners worldwide.
      </p>

      {!started ? (
        <div className="stripe-card" style={{ padding: 28, marginBottom: 24 }}>
          <div style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11, fontWeight: 500, color: '#64748d',
            textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 20,
          }}>
            Configuration
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 400, color: '#273951', marginBottom: 6 }}>
                Product
              </label>
              <input className="stripe-input" value={product} onChange={e => setProduct(e.target.value)} placeholder="caviar" />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 400, color: '#273951', marginBottom: 6 }}>
                Keyword (optional)
              </label>
              <input className="stripe-input" value={keyword} onChange={e => setKeyword(e.target.value)} placeholder="importer distributor" />
            </div>
          </div>

          <label style={{ display: 'block', fontSize: 13, fontWeight: 400, color: '#273951', marginBottom: 10 }}>
            Countries ({selected.length})
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 24 }}>
            {TIER1.map(c => {
              const on = selected.includes(c)
              return (
                <button key={c} onClick={() => setSelected(prev => on ? prev.filter(x => x !== c) : [...prev, c])} style={{
                  padding: '5px 14px', borderRadius: 6, border: on ? '1px solid #533afd' : '1px solid #e5edf5',
                  fontSize: 13, fontWeight: on ? 400 : 300, fontFamily: "'Inter', sans-serif",
                  color: on ? '#533afd' : '#64748d', background: on ? 'rgba(83,58,253,0.04)' : '#ffffff',
                  cursor: 'pointer', transition: 'all 0.12s',
                }}>
                  {c}
                </button>
              )
            })}
          </div>

          <button className="stripe-btn" onClick={() => setStarted(true)} style={{ fontSize: 16, padding: '12px 28px' }}>
            Start Search
          </button>
        </div>
      ) : (
        <SearchRunner product={product} keyword={keyword} countries={selected} onReset={() => setStarted(false)} />
      )}
    </div>
  )
}
