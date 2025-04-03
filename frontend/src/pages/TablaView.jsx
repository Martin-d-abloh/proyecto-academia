import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"

function TablaView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const token = localStorage.getItem("token")

  const [tabla, setTabla] = useState(null)
  const [nuevoDoc, setNuevoDoc] = useState("")
  const [nuevoAlumno, setNuevoAlumno] = useState({ nombre: "", apellidos: "" })
  const [mensaje, setMensaje] = useState("")

  useEffect(() => {
    console.log("🔁 Cargando tabla con ID:", id)
    console.log("🔐 Token actual:", token)

    fetch(`http://localhost:5001/api/admin/tabla/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        console.log("📡 Respuesta de la API:", res)
        return res.json()
      })
      .then((data) => {
        console.log("📦 Datos recibidos:", data)
        if (data.error) {
          console.warn("⚠️ Error recibido:", data.error)
          setMensaje("❌ No autorizado o acceso denegado")
          navigate("/")
          return
        }
        setTabla(data)
      })
      .catch((err) => console.error("❌ Error en fetch tabla:", err))
  }, [id, token])

  const añadirDocumento = async () => {
    if (!nuevoDoc) return
    const res = await fetch(`http://localhost:5001/api/admin/tabla/${id}/documento`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ nombre: nuevoDoc }),
    })
    const data = await res.json()
    if (res.ok) {
      setMensaje("✅ Documento añadido")
      setNuevoDoc("")
      location.reload()
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }

  const eliminarDocumento = async (docId) => {
    if (!confirm("¿Eliminar este documento?")) return
    await fetch(`http://localhost:5001/api/admin/tabla/${id}/documento/${docId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    })
    location.reload()
  }

  const eliminarAlumno = async (alumnoId) => {
    if (!confirm("¿Eliminar este alumno?")) return
    await fetch(`http://localhost:5001/api/admin/tabla/${id}/alumno/${alumnoId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    })
    location.reload()
  }

  const añadirAlumno = async () => {
    if (!nuevoAlumno.nombre || !nuevoAlumno.apellidos) {
      setMensaje("⚠️ Faltan nombre o apellidos")
      return
    }

    const res = await fetch(`http://localhost:5001/api/admin/tabla/${id}/alumnos`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(nuevoAlumno)
    })

    const data = await res.json()
    if (res.ok) {
      setMensaje("✅ Alumno añadido")
      setNuevoAlumno({ nombre: "", apellidos: "" })
      location.reload()
    } else {
      setMensaje(`❌ Error: ${data.error}`)
    }
  }

  if (!tabla) return <div>Cargando...</div>

  const documentosMap = {}
  for (const d of tabla.subidos) {
    if (!documentosMap[d.alumno_id]) documentosMap[d.alumno_id] = {}
    documentosMap[d.alumno_id][d.nombre] = d
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">{tabla.nombre}</h1>
      {mensaje && <div className="mb-4 text-green-600">{mensaje}</div>}

      <h2 className="text-xl font-semibold mt-4 mb-2">Alumnos</h2>
      <table className="w-full border">
        <thead>
          <tr>
            <th className="border px-2 py-1">Nombre</th>
            {tabla.documentos.map((doc) => (
              <th key={doc.id} className="border px-2 py-1">
                {doc.nombre}
                <button
                  className="ml-2 text-sm text-red-600"
                  onClick={() => eliminarDocumento(doc.id)}
                >
                  🗑️
                </button>
              </th>
            ))}
            <th className="border px-2 py-1">Estado</th>
            <th className="border px-2 py-1">Link</th>
            <th className="border px-2 py-1">Eliminar</th>
          </tr>
        </thead>
        <tbody>
          {tabla.alumnos.map((a) => (
            <tr key={a.id}>
              <td className="border px-2 py-1">{a.nombre} {a.apellidos}</td>
              {tabla.documentos.map((doc) => {
                const d = documentosMap[a.id]?.[doc.nombre]
                return (
                  <td key={doc.id} className="border px-2 py-1">
                    {d ? (
                      <>
                        {d.estado === "aceptado"
                          ? "✅ Validado"
                          : d.estado === "subido"
                          ? "✅ Subido"
                          : "❌ Rechazado"}
                        <br />
                        <a href={`http://localhost:5001/descargar/${d.id}`}>📥 Descargar</a>
                        </>
                    ) : (
                      "❌ No entregado"
                    )}
                  </td>
                )
              })}
              <td className="border px-2 py-1">
                {documentosMap[a.id] &&
                Object.keys(documentosMap[a.id]).length === tabla.documentos.length
                  ? "✅"
                  : "❌"}
              </td>
              <td className="border px-2 py-1">
                <a href={`/alumno/${a.id}`} className="text-blue-600 underline">
                  Acceder
                </a>
              </td>
              <td className="border px-2 py-1">
                <button
                  className="text-red-600"
                  onClick={() => eliminarAlumno(a.id)}
                >
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-2">Añadir nuevo documento</h3>
        <input
          type="text"
          value={nuevoDoc}
          onChange={(e) => setNuevoDoc(e.target.value)}
          placeholder="Nombre del documento"
          className="border px-2 py-1 mr-2"
        />
        <button
          onClick={añadirDocumento}
          className="bg-blue-600 text-white px-4 py-1 rounded"
        >
          Añadir
        </button>
      </div>

      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-2">Añadir nuevo alumno</h3>
        <input
          type="text"
          value={nuevoAlumno.nombre}
          onChange={(e) => setNuevoAlumno({ ...nuevoAlumno, nombre: e.target.value })}
          placeholder="Nombre"
          className="border px-2 py-1 mr-2"
        />
        <input
          type="text"
          value={nuevoAlumno.apellidos}
          onChange={(e) => setNuevoAlumno({ ...nuevoAlumno, apellidos: e.target.value })}
          placeholder="Apellidos"
          className="border px-2 py-1 mr-2"
        />
        <button
          onClick={añadirAlumno}
          className="bg-green-600 text-white px-4 py-1 rounded"
        >
          Añadir
        </button>
      </div>
    </div>
  )
}

export default TablaView
