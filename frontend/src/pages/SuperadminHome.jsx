import { useEffect, useState } from "react"

function SuperadminHome() {
  const [admins, setAdmins] = useState([])
  const [nuevoAdmin, setNuevoAdmin] = useState({ nombre: "", contraseña: "" })
  const [mensaje, setMensaje] = useState("")

  useEffect(() => {
    fetch("/api/superadmin/admins")
      .then((res) => res.json())
      .then((data) => setAdmins(data.admins))
      .catch((err) => console.error("Error cargando admins:", err))
  }, [])

  const crearAdmin = async () => {
    const res = await fetch("/api/superadmin/admins", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(nuevoAdmin),
    })

    const data = await res.json()
    if (res.ok) {
      setMensaje("✅ Admin creado")
      setNuevoAdmin({ nombre: "", contraseña: "" })
      const nuevos = await fetch("/api/superadmin/admins").then((r) => r.json())
      setAdmins(nuevos.admins)
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }

  const eliminarAdmin = async (id) => {
    const res = await fetch(`/api/superadmin/admins/${id}`, {
      method: "DELETE",
    })

    const data = await res.json()
    if (res.ok) {
      setMensaje("🗑️ Admin eliminado")
      const nuevos = await fetch("/api/superadmin/admins").then((r) => r.json())
      setAdmins(nuevos.admins)
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
            <button
              onClick={() => eliminarAdmin(admin.id)}
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

export default SuperadminHome
