import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"

function TablaView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const token = localStorage.getItem("token")

  const [tabla, setTabla] = useState({
    nombre: "",
    documentos: [],
    alumnos: [],
    subidos: []
  })
  const [nuevoDoc, setNuevoDoc] = useState("")
  const [nuevoAlumno, setNuevoAlumno] = useState({ nombre: "", apellidos: "" })
  const [mensaje, setMensaje] = useState("")

  useEffect(() => {
    const cargarTabla = async () => {
      try {
        const res = await fetch(`http://localhost:5001/api/admin/tabla/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
  
        if (!res.ok) {
          if (res.status === 403) {
            localStorage.removeItem("token")
            navigate("/")
          } else {
            const data = await res.json()
            setMensaje(`❌ Error: ${data.error || "No se pudo cargar la tabla"}`)
          }
          return
        }
  
        const data = await res.json()
        setTabla({
          nombre: data.nombre || "",
          documentos: data.documentos || [],
          alumnos: data.alumnos || [],
          subidos: data.subidos || []
        })
  
      } catch (error) {
        console.error("Error cargando tabla:", error)
        setMensaje("Error al cargar los datos")
      }
    }
  
    cargarTabla()
  }, [id, token])
  

  const añadirDocumento = async () => {
    if (!nuevoDoc) return
    try {
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
        setTabla(prev => ({
          ...prev,
          documentos: [...prev.documentos, data]
        }))
      } else {
        setMensaje(`❌ Error: ${data.error}`)
      }
    } catch (err) {
      console.error("Error añadiendo documento:", err)
    }
  }

  const eliminarDocumento = async (docId) => {
    if (!confirm("¿Eliminar este documento?")) return
    try {
      const backupEstado = structuredClone(tabla)
      
      setTabla(prev => ({
        ...prev,
        documentos: prev.documentos.filter(d => d.id !== docId),
        subidos: prev.subidos.filter(s => s.nombre !== docId)
      }))
  
      const res = await fetch(`http://localhost:5001/api/admin/tabla/${id}/documento/${docId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })
  
      if (!res.ok) throw new Error("Error del servidor")
      
      setMensaje("✅ Documento eliminado")
    } catch (err) {
      setTabla(backupEstado)
      setMensaje(`❌ Error: ${err.message}`)
    }
  }


const eliminarAlumno = async (alumnoId) => {
  if (!confirm("¿Eliminar este alumno permanentemente?")) return
  
  try {
    const token = localStorage.getItem("token_admin") || localStorage.getItem("token")
    const backupEstado = structuredClone(tabla) // 1. Backup del estado

    // 2. Eliminación optimista inmediata
    setTabla(prev => ({
      ...prev,
      alumnos: prev.alumnos.filter(a => a.id !== alumnoId),
      subidos: prev.subidos.filter(s => s.alumno_id !== alumnoId)
    }))

    // 3. Petición al backend
    const res = await fetch(`http://localhost:5001/api/admin/tabla/${id}/alumno/${alumnoId}`, {
      method: "DELETE",
      headers: { 
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    })

    // 4. Manejo de respuesta
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ error: "Error desconocido" }))
      throw new Error(errorData.error || `Error HTTP: ${res.status}`)
    }

    setMensaje("✅ Alumno eliminado exitosamente")

  } catch (err) {
    // 5. Rollback automático con feedback
    console.error("Error en eliminación:", err)
    setTabla(backupEstado)
    setMensaje(`❌ ${err.message || "Error al eliminar"}`)
    
    // 6. Recarga segura solo para errores críticos
    if (err.message.includes("Token") || err.message.includes("permiso")) {
      setTimeout(() => location.reload(), 2000)
    }
  }
}
  

  const añadirAlumno = async () => {
    if (!nuevoAlumno.nombre || !nuevoAlumno.apellidos) {
      setMensaje("⚠️ Faltan nombre o apellidos")
      return
    }

    try {
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
        setTabla(prev => ({
          ...prev,
          alumnos: [...prev.alumnos, data]
        }))
      } else {
        setMensaje(`❌ Error: ${data.error}`)
      }
    } catch (err) {
      console.error("Error añadiendo alumno:", err)
    }
  }

  const documentosMap = tabla.subidos.reduce((acc, d) => {
    acc[d.alumno_id] = acc[d.alumno_id] || {}
    acc[d.alumno_id][d.nombre] = d
    return acc
  }, {})

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">{tabla.nombre}</h1>
      {mensaje && <div className="mb-4 text-green-600">{mensaje}</div>}

      <h2 className="text-xl font-semibold mt-4 mb-2">Alumnos</h2>
      <table className="w-full border">
        <thead>
          <tr>
            <th className="border px-2 py-1">Nombre</th>
            {tabla.documentos?.map((doc) => (
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
          {tabla.alumnos?.map((a) => (
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