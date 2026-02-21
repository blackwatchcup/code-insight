import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Projects from './pages/Projects'
import Login from './pages/Login'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'
import { useAuthStore } from './stores/authStore'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, fetchUser, isLoading } = useAuthStore()
  const [checking, setChecking] = useState(true)
  
  useEffect(() => {
    const checkAuth = async () => {
      await fetchUser()
      setChecking(false)
    }
    checkAuth()
  }, [fetchUser])
  
  if (checking) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600"></div>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

export default function App() {
  const [activeTab, setActiveTab] = useState('projects')
  const { isAuthenticated, logout, user } = useAuthStore()

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={
          isAuthenticated ? <Navigate to="/" replace /> : <Login />
        } />
        <Route path="/*" element={
          <PrivateRoute>
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex flex-col">
              <Navbar user={user} onLogout={logout} />
              <div className="flex flex-1 overflow-hidden">
                <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
                <main className="flex-1 overflow-y-auto">
                  <Routes>
                    <Route path="/" element={<Projects />} />
                  </Routes>
                </main>
              </div>
            </div>
          </PrivateRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}
