import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"

function AdminHome() {
  const [tablas, setTablas] = useState([])
  const [nuevaTabla, setNuevaTabla] = useState("")
  const [mensaje, setMensaje] = useState("")
  const navigate = useNavigate()
  const { id } = useParams()

  const token = localStorage.getItem("token")

  useEffect(() => {
    const url = id
      ? `${import.meta.env.VITE_BACKEND_URL}/api/admin/tablas?admin_id=${id}`
      : `${import.meta.env.VITE_BACKEND_URL}/api/admin/tablas`
  
    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setMensaje(`❌ ${data.error}`)
          setTablas([])
        } else {
          setTablas(data.tablas || [])
        }
      })
      .catch((err) => {
        console.error("Error cargando tablas:", err)
        setMensaje("❌ Error cargando tablas")
      })
  }, [token, id])
  
  const crearTabla = async () => {
    if (!nuevaTabla) return
  
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/admin/tablas`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ nombre: nuevaTabla })
    })
  
    const data = await res.json()
    if (res.ok) {
      setMensaje("✅ Tabla creada")
      setNuevaTabla("")
      const nuevas = await fetch(
        id
          ? `${import.meta.env.VITE_BACKEND_URL}/api/admin/tablas?admin_id=${id}`
          : `${import.meta.env.VITE_BACKEND_URL}/api/admin/tablas`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      ).then((r) => r.json())
      setTablas(nuevas.tablas || [])
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }
  
  const eliminarTabla = async (tablaId) => {
    const confirmar = window.confirm("¿Estás seguro de que quieres eliminar esta tabla? Esta acción no se puede deshacer.");
    if (!confirmar) return;
  
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/admin/tabla/${tablaId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
  
    const data = await res.json()
    if (res.ok) {
      setMensaje("🗑️ Tabla eliminada")
      const nuevas = await fetch(
        id
          ? `${import.meta.env.VITE_BACKEND_URL}/api/admin/tablas?admin_id=${id}`
          : `${import.meta.env.VITE_BACKEND_URL}/api/admin/tablas`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      ).then((r) => r.json())
      setTablas(nuevas.tablas || [])
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }
  
  

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-blue-100 p-6">
      <h1 className="text-4xl font-black text-blue-800 mb-6 drop-shadow">
        🛠️ Panel del Administrador
      </h1>

      {mensaje && (
        <div className="mb-6 text-lg font-semibold px-4 py-2 rounded bg-white border-l-4 border-blue-500 shadow">
          {mensaje}
        </div>
      )}

      <div className="mb-8">
        <h2 className="text-2xl font-bold text-blue-700 mb-3">➕ Crear nueva tabla</h2>
        <div className="flex flex-wrap gap-3 items-center">
          <input
            type="text"
            placeholder="Nombre de nueva tabla"
            value={nuevaTabla}
            onChange={(e) => setNuevaTabla(e.target.value)}
            className="px-4 py-2 rounded border w-full sm:w-auto"
          />
          <button
            onClick={crearTabla}
            className="bg-blue-600 text-white font-semibold px-5 py-2 rounded hover:bg-blue-700 shadow"
          >
            Crear tabla
          </button>
        </div>
      </div>

      <h2 className="text-2xl font-bold text-blue-700 mb-4">📋 Tus tablas</h2>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tablas.map((tabla) => (
          <li
            key={tabla.id}
            className="bg-white border-l-4 border-blue-400 p-4 rounded-xl shadow hover:shadow-md flex flex-col justify-between"
          >
            <div
              className="text-lg font-medium text-gray-800 mb-3 cursor-pointer hover:underline"
              onClick={() => navigate(`/admin/tabla/${tabla.id}`)}
            >
              📁 {tabla.nombre}
            </div>
            <div>
              <button
                onClick={() => eliminarTabla(tabla.id)}
                className="bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200"
              >
                Eliminar
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default AdminHome
