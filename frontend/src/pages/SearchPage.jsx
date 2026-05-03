import { useState } from 'react'
import SearchRunner from '../components/SearchRunner'

export default function SearchPage() {
  const [product, setProduct] = useState('caviar')
  const [keyword, setKeyword] = useState('')
  const [selectedCountries, setSelectedCountries] = useState(['France', 'Spain', 'Italy', 'Germany', 'Japan'])
  const [started, setStarted] = useState(false)

  const tier1 = ['France','USA','Italy','Germany','Spain','Japan','United Kingdom','Switzerland','UAE','Netherlands','Belgium','Australia','Canada','Singapore','Hong Kong']

  const toggle = (code) => {
    setSelectedCountries(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    )
  }

  return (
    <div style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.03em', color: '#171717', marginBottom: 8 }}>
        Search
      </h1>
      <p style={{ fontSize: 14, color: '#808080', marginBottom: 24 }}>
        AI-powered B2B customer discovery for premium caviar trade.
      </p>

      {!started ? (
        <div className="vercel-card" style={{ padding: '24px', marginBottom: 24 }}>
          <span className="vercel-mono" style={{ display: 'block', marginBottom: 16 }}>Configuration</span>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: '#808080', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 6 }}>
                Product
              </label>
              <input className="vercel-input" value={product} onChange={e => setProduct(e.target.value)}
                placeholder="caviar" style={{ width: '100%' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: '#808080', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 6 }}>
                Keyword (optional)
              </label>
              <input className="vercel-input" value={keyword} onChange={e => setKeyword(e.target.value)}
                placeholder="importer distributor" style={{ width: '100%' }} />
            </div>
          </div>

          <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: '#808080', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>
            Countries ({selectedCountries.length} selected)
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 20 }}>
            {tier1.map(c => {
              const sel = selectedCountries.includes(c)
              return (
                <button key={c} onClick={() => toggle(c)} style={{
                  padding: '4px 12px',
                  borderRadius: '9999px',
                  border: 'none',
                  fontSize: 13,
                  fontWeight: sel ? 500 : 400,
                  fontFamily: "'Inter', sans-serif",
                  color: sel ? '#ffffff' : '#666666',
                  background: sel ? '#171717' : '#f5f5f5',
                  cursor: 'pointer',
                  transition: 'all 0.1s',
                }}>
                  {c}
                </button>
              )
            })}
          </div>

          <button className="vercel-btn-dark" onClick={() => setStarted(true)}
            style={{ fontSize: 15, padding: '10px 24px' }}>
            Start Search
          </button>
        </div>
      ) : (
        <SearchRunner
          product={product}
          keyword={keyword}
          countries={selectedCountries}
          onReset={() => setStarted(false)}
        />
      )}
    </div>
  )
}
