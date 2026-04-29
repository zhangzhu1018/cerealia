import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { ToastProvider } from './components/ui/Toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import CustomerList from './pages/CustomerList'
import CustomerDetail from './pages/CustomerDetail'
import CustomerImportPage from './pages/CustomerImportPage'
import EmailPage from './pages/EmailPage'
import EmailSettingsPage from './pages/EmailSettingsPage'
import SearchPage from './pages/SearchPage'
import ScoringPage from './pages/ScoringPage'
import ActivitiesPage from './pages/ActivitiesPage'
import LoginPage from './pages/LoginPage'

// ── 路由守卫：未登录 → 跳转 /login ──────────────────────────────────────
function RequireAuth({ children }) {
  const token = localStorage.getItem('caviar_token')
  const location = useLocation()
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return children
}

function PublicOnly({ children }) {
  const token = localStorage.getItem('caviar_token')
  if (token) {
    return <Navigate to="/" replace />
  }
  return children
}

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        {/* 登录页面（已登录则重定向首页） */}
        <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />

        {/* 受保护的页面 */}
        <Route element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }>
          <Route path="/" element={<Dashboard />} />
          <Route path="/customers" element={<CustomerList />} />
          <Route path="/customers/:id" element={<CustomerDetail />} />
          <Route path="/customers/import" element={<CustomerImportPage />} />
          <Route path="/emails" element={<EmailPage />} />
          <Route path="/email-settings" element={<EmailSettingsPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/scoring" element={<ScoringPage />} />
          <Route path="/activities" element={<ActivitiesPage />} />
        </Route>

        {/* 兜底：未匹配 → 首页 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ToastProvider>
  )
}
