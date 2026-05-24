import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ProjectView from './pages/ProjectView'

export default function App() {
  return (
    <Routes>
      <Route path="/"            element={<Dashboard />} />
      <Route path="/project/:docId" element={<ProjectView />} />
    </Routes>
  )
}
