import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"

function AdminHome() {
  const [tablas, setTablas] = useState([])
  const [nuevaTabla, setNuevaTabla] = useState("")
  const [mensaje, setMensaje] = useState("")
  const navigate = useNavigate()
  const { id } = useParams()  // Si el superadmin accede al panel de un admin

  const token = localStorage.getItem("token")

  useEffect(() => {
    const url = id
      ? `http://localhost:5001/api/admin/tablas?admin_id=${id}`
      : `http://localhost:5001/api/admin/tablas`

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

    const res = await fetch("http://localhost:5001/api/admin/tablas", {
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
          ? `http://localhost:5001/api/admin/tablas?admin_id=${id}`
          : "http://localhost:5001/api/admin/tablas",
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
    const res = await fetch(`http://localhost:5001/api/admin/tabla/${tablaId}`, {
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
          ? `http://localhost:5001/api/admin/tablas?admin_id=${id}`
          : "http://localhost:5001/api/admin/tablas",
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
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-3xl font-bold text-blue-700 mb-4">
        Panel del Administrador 🛠️
      </h1>

      {mensaje && <p className="mb-4">{mensaje}</p>}

      <div className="mb-6">
        <input
          type="text"
          placeholder="Nombre de nueva tabla"
          value={nuevaTabla}
          onChange={(e) => setNuevaTabla(e.target.value)}
          className="px-3 py-1 border rounded mr-2"
        />
        <button
          onClick={crearTabla}
          className="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700"
        >
          Crear tabla
        </button>
      </div>

      <h2 className="text-xl font-semibold mb-2">Tus tablas:</h2>
      <ul className="space-y-3">
        {tablas.map((tabla) => (
          <li
            key={tabla.id}
            className="bg-white p-4 rounded shadow flex justify-between items-center"
          >
            <span
              className="cursor-pointer hover:underline"
              onClick={() => navigate(`/admin/tabla/${tabla.id}`)}
            >
              📁 {tabla.nombre}
            </span>
            <button
              onClick={() => eliminarTabla(tabla.id)}
              className="text-red-600 underline"
            >
              Eliminar
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default AdminHome
