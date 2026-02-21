import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import Projects from './pages/Projects'
import Login from './pages/Login'
import Chat from './pages/Chat'
import Analysis from './pages/Analysis'
import ProjectDetail from './pages/ProjectDetail'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'
import { useAuthStore } from './stores/authStore'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, fetchUser } = useAuthStore()
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

function AppContent() {
  const [activeTab, setActiveTab] = useState('projects')
  const { logout, user } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    if (location.pathname === '/') {
      setActiveTab('projects')
    } else if (location.pathname.startsWith('/chat')) {
      setActiveTab('chat')
    } else if (location.pathname.startsWith('/project')) {
      setActiveTab('projects')
    } else if (location.pathname.startsWith('/analysis')) {
      setActiveTab('analysis')
    }
  }, [location.pathname])

  const handleTabChange = (tab: string) => {
    setActiveTab(tab)
    switch (tab) {
      case 'projects':
        navigate('/')
        break
      case 'chat':
        navigate('/chat')
        break
      case 'analysis':
        navigate('/analysis')
        break
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex flex-col">
      <Navbar user={user} onLogout={logout} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Projects />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/chat/:projectId" element={<Chat />} />
            <Route path="/project/:id" element={<ProjectDetail />} />
            <Route path="/analysis" element={<Analysis />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={
          <PrivateRoute>
            <AppContent />
          </PrivateRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}
