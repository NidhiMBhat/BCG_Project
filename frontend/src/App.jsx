import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PatientsPage from './pages/PatientsPage'
import PatientDetailPage from './pages/PatientDetailPage'
import LiveMonitorPage from './pages/LiveMonitorPage'
import AnalyticsPage from './pages/AnalyticsPage'
import HistoryPage from './pages/HistoryPage'
import ExportsPage from './pages/ExportsPage'
import SettingsPage from './pages/SettingsPage'

function ProtectedLayout({ children }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}

function AppRoutes() {
  const { isAuthenticated } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
      <Route path="/patients" element={<ProtectedLayout><PatientsPage /></ProtectedLayout>} />
      <Route path="/patients/:id" element={<ProtectedLayout><PatientDetailPage /></ProtectedLayout>} />
      <Route path="/live" element={<ProtectedLayout><LiveMonitorPage /></ProtectedLayout>} />
      <Route path="/analytics" element={<ProtectedLayout><AnalyticsPage /></ProtectedLayout>} />
      <Route path="/history" element={<ProtectedLayout><HistoryPage /></ProtectedLayout>} />
      <Route path="/exports" element={<ProtectedLayout><ExportsPage /></ProtectedLayout>} />
      <Route path="/settings" element={<ProtectedLayout><SettingsPage /></ProtectedLayout>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
