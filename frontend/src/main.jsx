import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Login from './pages/Login'
import AdminHome from './pages/AdminHome'
import SuperadminHome from './pages/SuperadminHome'
import AlumnoPanel from './pages/AlumnoPanel'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login tipo="admin" />} />
        <Route path="/admin" element={<AdminHome />} />
        <Route path="/superadmin" element={<SuperadminHome />} />
        <Route path="/alumno" element={<AlumnoPanel />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
)

