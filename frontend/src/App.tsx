import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Projects from './pages/Projects'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'

export default function App() {
  const [activeTab, setActiveTab] = useState('projects')

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex flex-col">
        <Navbar />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Projects />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
