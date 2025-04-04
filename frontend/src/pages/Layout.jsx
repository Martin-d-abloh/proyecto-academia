import { Outlet, useNavigate, useLocation } from "react-router-dom"
import { useEffect, useState } from "react"

function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [mostrarLogout, setMostrarLogout] = useState(false)
  const [mostrarCabecera, setMostrarCabecera] = useState(true)

  const cerrarSesion = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("token_superadmin")
    navigate("/")
  }

  useEffect(() => {
    const token =
      localStorage.getItem("token") ||
      localStorage.getItem("token_superadmin")

    const esVistaLogin =
      location.pathname === "/" ||
      location.pathname === "/login" ||
      location.pathname === "/login_alumno"

    const esVistaAlumno = location.pathname.includes("/alumno")

    setMostrarLogout(token && !esVistaLogin && !esVistaAlumno)
    setMostrarCabecera(!esVistaLogin && !esVistaAlumno)
  }, [location])

  return (
    <div className="min-h-screen bg-gray-100 text-gray-800 font-sans">
      {mostrarCabecera && (
        <header className="bg-white shadow p-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-blue-700">Panel de Gestión</h1>
          {mostrarLogout && (
            <button
              onClick={cerrarSesion}
              className="bg-red-600 text-white px-4 py-1 rounded hover:bg-red-700"
            >
              Cerrar sesión
            </button>
          )}
        </header>
      )}

      <main className="max-w-5xl mx-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}


export default Layout
