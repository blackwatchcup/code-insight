import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Projects from './pages/Projects'
import Navbar from './components/Navbar'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Projects />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
