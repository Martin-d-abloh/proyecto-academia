import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

function SuperadminHome() {
  const [admins, setAdmins] = useState([])
  const [nuevoAdmin, setNuevoAdmin] = useState({ nombre: "", contraseña: "" })
  const [mensaje, setMensaje] = useState("")
  const token = localStorage.getItem("token")
  const superadminNombre = "Super Admin" // 👑 Nombre exacto del superadmin
  const navigate = useNavigate()

  useEffect(() => {
    cargarAdmins()
  }, [])

  const cargarAdmins = () => {
    fetch("http://localhost:5001/api/superadmin/admins", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => res.json())
      .then((data) => setAdmins(data.admins))
      .catch((err) => console.error("Error cargando admins:", err))
  }

  const crearAdmin = async () => {
    const res = await fetch("http://localhost:5001/api/superadmin/admins", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(nuevoAdmin),
    })

    const data = await res.json()
    if (res.ok) {
      setMensaje("✅ Admin creado")
      setNuevoAdmin({ nombre: "", contraseña: "" })
      cargarAdmins()
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }

  const eliminarAdmin = async (id) => {
    const res = await fetch(`http://localhost:5001/api/superadmin/admins/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    const data = await res.json()
    if (res.ok) {
      setMensaje("🗑️ Admin eliminado")
      cargarAdmins()
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }

  return (
    <div className="min-h-screen bg-blue-50 p-6">
      <h1 className="text-3xl font-bold text-blue-700 mb-4">
        Panel del Superadmin 👑
      </h1>

      {mensaje && <p className="mb-4">{mensaje}</p>}

      <h2 className="text-xl font-semibold mb-2">Crear nuevo administrador:</h2>
      <div className="flex space-x-2 mb-4">
        <input
          type="text"
          placeholder="Nombre"
          value={nuevoAdmin.nombre}
          onChange={(e) =>
            setNuevoAdmin({ ...nuevoAdmin, nombre: e.target.value })
          }
          className="px-3 py-1 border rounded"
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={nuevoAdmin.contraseña}
          onChange={(e) =>
            setNuevoAdmin({ ...nuevoAdmin, contraseña: e.target.value })
          }
          className="px-3 py-1 border rounded"
        />
        <button
          onClick={crearAdmin}
          className="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700"
        >
          Crear
        </button>
      </div>

      <h2 className="text-xl font-semibold mb-2">Administradores actuales:</h2>
      <ul className="space-y-2">
        {admins.map((admin) => (
          <li
            key={admin.id}
            className="bg-white p-3 rounded shadow flex justify-between items-center"
          >
            <span>{admin.nombre}</span>
            <div className="flex space-x-2">
              <button
                onClick={() => navigate(`/admin/tabla/${admin.id}`)}
                className="text-blue-600 underline"
              >
                Ver
              </button>

              {admin.nombre !== superadminNombre && (
                <button
                  onClick={() => eliminarAdmin(admin.id)}
                  className="text-red-600 underline"
                >
                  Eliminar
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default SuperadminHome
