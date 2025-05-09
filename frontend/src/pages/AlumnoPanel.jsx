import { useParams, useNavigate } from "react-router-dom"
import { useEffect, useState } from "react"


function AlumnoPanel() {
  const { id } = useParams()
  const [documentos, setDocumentos] = useState([])
  const [archivos, setArchivos] = useState({})
  const [mensaje, setMensaje] = useState("")
  const [alumno, setAlumno] = useState({ nombre: "", apellidos: "" })
  const [alumnoCargando, setAlumnoCargando] = useState(true)
  const [alumnoError, setAlumnoError] = useState("")
  const navigate = useNavigate()

  useEffect(() => {
    const token = localStorage.getItem("token_alumno")
    if (!token) {
      navigate("/login_alumno")
      return
    }

    // Obtener datos del alumno
    const cargarAlumno = async () => {
      setAlumnoCargando(true)
      setAlumnoError("")
      try {
        const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/alumno/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const data = await res.json()
        console.log("Respuesta API alumno:", data)
        if (res.ok && data.nombre) {
          setAlumno({ nombre: data.nombre, apellidos: data.apellidos })
        } else {
          setAlumnoError(data.error || "No se pudo obtener el nombre del alumno")
        }
      } catch (err) {
        setAlumnoError("Error de red o backend al obtener el alumno")
        console.error("No se pudo cargar el nombre del alumno", err)
      } finally {
        setAlumnoCargando(false)
      }
    }
    cargarAlumno()

    const cargarDocumentos = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/alumno/${id}/documentos`, {
          headers: { Authorization: `Bearer ${token}` }
        })
    
        if (!response.ok) {
          const text = await response.text()
          console.error("Respuesta completa del backend:", text)
    
          if (response.status === 403) {
            localStorage.removeItem("token_alumno")
            navigate("/login_alumno")
            return
          }
    
          throw new Error("Error del backend al cargar documentos")
        }
    
        const data = await response.json()
        setDocumentos(data.documentos || [])
      } catch (err) {
        console.error("Error cargando documentos:", err)
        setMensaje(`❌ ${err.message}`)
      }
    }
    
    cargarDocumentos()
    }, [id, navigate])
    
    const handleFileChange = (nombre, archivo) => {
      setArchivos(prev => ({ ...prev, [nombre]: archivo }))
    }
    
    const actualizarDocumentos = async () => {
      const token = localStorage.getItem("token_alumno")
      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/alumno/${id}/documentos`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await response.json()
      setDocumentos(data.documentos)
    }
    
    const verDocumento = (docId) => {
      const token = localStorage.getItem("token_alumno")
      const url = `${import.meta.env.VITE_BACKEND_URL}/api/alumno/ver/${docId}?token=${token}`
      window.open(url, "_blank")
    }
    
    const handleUpload = async (nombre) => {
      try {
        const archivo = archivos[nombre]
        if (!archivo) {
          setMensaje("⚠️ Selecciona un archivo antes de subir.")
          return
        }
    
        const formData = new FormData()
        formData.append("archivo", archivo)
        formData.append("nombre_documento", nombre)
    
        const token = localStorage.getItem("token_alumno")
        const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/alumno/${id}/subir`, {
          method: "POST",
          body: formData,
          headers: { Authorization: `Bearer ${token}` }
        })
    
        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.error || "Error al subir el documento")
        }
    
        setMensaje("✅ Documento subido correctamente.")
        await actualizarDocumentos()
    
      } catch (err) {
        console.error("Error en subida:", err)
        setMensaje(`❌ Error: ${err.message}`)
      }
    }
    
    const eliminarDocumento = async (docId) => {
      try {
        const token = localStorage.getItem("token_alumno")
        const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/alumno/${id}/documentos/${docId}/eliminar`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        })
    
        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.error || "Error al eliminar")
        }
    
        await actualizarDocumentos()
        setMensaje("🗑️ Documento eliminado.")
    
      } catch (err) {
        console.error("Error eliminando:", err)
        setMensaje(`❌ Error: ${err.message}`)
      }
    }
    

  return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 p-6">
        <h1 className="text-3xl font-black text-green-700 mb-2">🎓 Panel del Alumno</h1>
        {alumno.nombre && (
          <h2 className="text-xl font-semibold text-green-800 mb-6">Alumno: {alumno.nombre} {alumno.apellidos}</h2>
        )}
    
        {mensaje && (
          <p className="mb-4 text-center text-green-800 font-medium bg-white border-l-4 border-green-500 p-3 rounded shadow-sm">
            {mensaje}
          </p>
        )}
    
        {documentos.length === 0 && (
          <p className="text-center text-gray-600 mt-4">
            📭 No hay documentos requeridos en este momento. Espera a que tu administrador los configure.
          </p>
        )}
    
        {documentos.map((doc) => (
          <div key={doc.id || doc.nombre} className="bg-white p-5 rounded-xl shadow-md mb-6 border-l-4 border-green-300">
            <h2 className="text-xl font-bold text-green-800 mb-1">📁 {doc.nombre}</h2>
            <p className="mb-2">
              Estado:{" "}
              {doc.estado === "subido" && <span className="text-blue-600 font-semibold">📄 Subido</span>}
              {doc.estado === "aceptado" && <span className="text-green-600 font-semibold">✅ Aceptado</span>}
              {doc.estado === "rechazado" && <span className="text-red-600 font-semibold">❌ Rechazado</span>}
              {doc.estado === "no_subido" && <span className="text-yellow-600 font-semibold">⚠️ No subido</span>}
            </p>
    
            {doc.subido && (
              <div className="flex items-center space-x-4 mt-2">
                <button
                  onClick={() => verDocumento(doc.id)}
                  className="bg-blue-100 text-blue-700 px-4 py-1 rounded hover:bg-blue-200 text-sm"
                >
                  👁️ Ver documento
                </button>
                <button
                  onClick={() => eliminarDocumento(doc.id)}
                  className="bg-red-100 text-red-700 px-4 py-1 rounded hover:bg-red-200 text-sm"
                >
                  🗑️ Eliminar documento
                </button>
              </div>
            )}
    
            <div className="mt-4">
              <input
                type="file"
                onChange={(e) => handleFileChange(doc.nombre, e.target.files[0])}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
              />
              <button
                onClick={() => handleUpload(doc.nombre)}
                className="mt-3 w-full bg-green-600 text-white font-semibold px-4 py-2 rounded hover:bg-green-700 shadow"
              >
                🚀 Subir documento
              </button>
            </div>
          </div>
        ))}
    
        <div className="mt-8 text-center">
          <button
            onClick={() => {
              localStorage.removeItem("token_alumno")
              navigate("/login_alumno")
            }}
            className="bg-red-100 text-red-700 px-4 py-2 rounded hover:bg-red-200 shadow"
          >
            🔒 Cerrar sesión
          </button>
        </div>
      </div>
    )
  }
  export default AlumnoPanel
