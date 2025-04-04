import { useParams, useNavigate } from "react-router-dom"
import { useEffect, useState } from "react"

function AlumnoPanel() {
  const { id } = useParams()
  const [documentos, setDocumentos] = useState([])
  const [archivos, setArchivos] = useState({})
  const [mensaje, setMensaje] = useState("")
  const navigate = useNavigate()

  useEffect(() => {
    const cargarDocumentos = async () => {
      const token = localStorage.getItem("token_alumno")
  
      if (!token) {
        navigate("/login_alumno")
        return
      }
  
      try {
        const response = await fetch(`http://localhost:5001/api/alumno/${id}/documentos`, {
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
    const response = await fetch(`http://localhost:5001/api/alumno/${id}/documentos`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = await response.json()
    setDocumentos(data.documentos)
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
      const res = await fetch(`http://localhost:5001/api/alumno/${id}/subir`, {
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
      const res = await fetch(`http://localhost:5001/api/alumno/${id}/documentos/${docId}/eliminar`, {
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
    <div className="min-h-screen bg-green-50 p-6">
      <h1 className="text-3xl font-bold text-green-700 mb-6">
        Panel del Alumno #{id}
      </h1>

      {mensaje && <p className="mb-4 text-center text-red-600">{mensaje}</p>}

      {documentos.length === 0 && (
        <p className="text-center text-gray-600 mt-4">
          📭 No hay documentos requeridos en este momento. Espera a que tu administrador los configure.
        </p>
      )}

      {documentos.map((doc) => (
        <div key={doc.id || doc.nombre} className="bg-white p-4 rounded-lg shadow mb-4">
          <h2 className="text-xl font-semibold">{doc.nombre}</h2>
          <p className="mb-2">
            Estado:{" "}
            {doc.estado === "subido" && "📄 Subido"}
            {doc.estado === "aceptado" && "✅ Aceptado"}
            {doc.estado === "rechazado" && "❌ Rechazado"}
            {doc.estado === "no_subido" && "⚠️ No subido"}
          </p>

          {doc.subido && (
            <div className="flex items-center space-x-4 mt-2">
              <a
                href={`/descargar/${doc.id}`}
                className="text-blue-600 hover:text-blue-800 underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                📥 Descargar
              </a>
              <button
                onClick={() => eliminarDocumento(doc.id)}
                className="text-red-600 hover:text-red-800 underline"
              >
                Eliminar documento
              </button>
            </div>
          )}

          <div className="mt-3">
            <input
              type="file"
              onChange={(e) => handleFileChange(doc.nombre, e.target.files[0])}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
            />
            <button
              onClick={() => handleUpload(doc.nombre)}
              className="mt-2 w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
            >
              Subir documento
            </button>
          </div>
        </div>
      ))}

      <div className="mt-6 text-center">
        <button
          onClick={() => {
            localStorage.removeItem("token_alumno")
            navigate("/login_alumno")
          }}
          className="text-red-600 hover:text-red-800 underline"
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}

export default AlumnoPanel
