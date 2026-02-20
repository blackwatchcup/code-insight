import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Projects from './pages/Projects'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Projects />} />
      </Routes>
    </BrowserRouter>
  )
}
