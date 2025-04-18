import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

function SuperadminHome() {
  const [admins, setAdmins] = useState([])
  const [nuevoAdmin, setNuevoAdmin] = useState({ nombre: "", usuario: "", contraseña: "" })
  const [mensaje, setMensaje] = useState("")
  const token = localStorage.getItem("token")
  const superadminNombre = "Super Admin"
  const navigate = useNavigate()

  useEffect(() => {
    cargarAdmins()
  }, [])

  const cargarAdmins = () => {
    fetch(`${import.meta.env.VITE_BACKEND_URL}/api/superadmin/admins`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => setAdmins(data.admins))
      .catch((err) => console.error("Error cargando admins:", err))
  }
  
  const crearAdmin = async () => {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/superadmin/admins`, {
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
      setNuevoAdmin({ nombre: "", usuario: "", contraseña: "" })
      cargarAdmins()
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }
  
  const eliminarAdmin = async (id) => {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/superadmin/admins/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    })
  
    const data = await res.json()
    if (res.ok) {
      setMensaje("🗑️ Admin eliminado")
      cargarAdmins()
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }
  
  const verPanelDeAdmin = async (adminId) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/superadmin/panel_admin/${adminId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
  
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "No se pudo acceder")
  
      navigate(`/admin/${adminId}`)
    } catch (err) {
      console.error("Error accediendo al panel del admin:", err)
      setMensaje(`❌ ${err.message}`)
    }
  }
  

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 to-indigo-200 p-6">
      <h1 className="text-4xl font-black text-indigo-800 mb-6 drop-shadow">
        👑 Superadmin Panel
      </h1>

      {mensaje && (
        <div className="mb-6 text-lg font-semibold px-4 py-2 rounded bg-white border-l-4 border-indigo-500 shadow">
          {mensaje}
        </div>
      )}

      <section className="mb-8">
        <h2 className="text-2xl font-bold text-indigo-700 mb-3">➕ Crear nuevo administrador</h2>
        <div className="flex flex-wrap gap-3 items-center">
          <input
            type="text"
            placeholder="Nombre"
            value={nuevoAdmin.nombre}
            onChange={(e) => setNuevoAdmin({ ...nuevoAdmin, nombre: e.target.value })}
            className="px-4 py-2 rounded border w-full sm:w-auto"
          />
          <input
            type="text"
            placeholder="Usuario"
            value={nuevoAdmin.usuario}
            onChange={(e) => setNuevoAdmin({ ...nuevoAdmin, usuario: e.target.value })}
            className="px-4 py-2 rounded border w-full sm:w-auto"
          />
          <input
            type="password"
            placeholder="Contraseña"
            value={nuevoAdmin.contraseña}
            onChange={(e) => setNuevoAdmin({ ...nuevoAdmin, contraseña: e.target.value })}
            className="px-4 py-2 rounded border w-full sm:w-auto"
          />
          <button
            onClick={crearAdmin}
            className="bg-indigo-600 text-white font-semibold px-5 py-2 rounded hover:bg-indigo-700 shadow"
          >
            Crear
          </button>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold text-indigo-700 mb-4">📋 Administradores actuales</h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {admins.map((admin) => (
            <li
              key={admin.id}
              className="bg-white border-l-4 border-indigo-400 p-4 rounded-xl shadow hover:shadow-md flex flex-col justify-between"
            >
              <div className="text-lg font-medium text-gray-800 mb-3">{admin.nombre}</div>
              <div className="flex gap-3">
                <button
                  onClick={() => verPanelDeAdmin(admin.id)}
                  className="bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200"
                >
                  Ver panel
                </button>
                {admin.nombre !== superadminNombre && (
                  <button
                    onClick={() => eliminarAdmin(admin.id)}
                    className="bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200"
                  >
                    Eliminar
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

export default SuperadminHome
