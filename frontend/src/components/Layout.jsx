import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#ffffff' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        marginLeft: 220,
        padding: '32px 40px',
        maxWidth: 1200,
        background: '#ffffff',
        minHeight: '100vh',
      }}>
        <Outlet />
      </main>
    </div>
  )
}
