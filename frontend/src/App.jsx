import { Routes, Route, Navigate } from 'react-router-dom'
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

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Layout />}>
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
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ToastProvider>
  )
}
