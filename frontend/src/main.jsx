import './index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Login from './pages/Login'
import AdminHome from './pages/AdminHome'
import SuperadminHome from './pages/SuperadminHome'
import AlumnoPanel from './pages/AlumnoPanel'
import Layout from './pages/Layout'
import TablaView from './pages/TablaView'
import LoginAlumno from './pages/LoginAlumno' // Asegúrate de importar el componente

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Ruta para login de alumnos (fuera del Layout) */}
        <Route path="/login_alumno" element={<LoginAlumno />} />
        
        <Route path="/" element={<Layout />}>
          <Route index element={<Login tipo="admin" />} />
          <Route path="admin" element={<AdminHome />} />
          <Route path="admin/:id" element={<AdminHome />} />
          <Route path="superadmin" element={<SuperadminHome />} />
          <Route path="admin/tabla/:id" element={<TablaView />} />
          <Route path="alumno/:id" element={<AlumnoPanel />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
)