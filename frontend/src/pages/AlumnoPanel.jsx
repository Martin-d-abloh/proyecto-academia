import { useParams } from "react-router-dom"
import { useEffect, useState } from "react"

function AlumnoPanel() {
  // Obtener el ID del alumno de los parámetros de la URL
  const { id } = useParams()
  
  // Estados para manejar los documentos, archivos y mensajes
  const [documentos, setDocumentos] = useState([])
  const [archivos, setArchivos] = useState({})
  const [mensaje, setMensaje] = useState("")

  // Efecto para cargar los documentos del alumno al montar el componente
  useEffect(() => {
    fetch(`/api/alumno/${id}/documentos`)
      .then(res => res.json())
      .then(data => setDocumentos(data.documentos))
      .catch(err => console.error("Error cargando documentos:", err))
  }, [id])

  // Manejar cambios en los inputs de archivos
  const handleFileChange = (nombre, archivo) => {
    setArchivos(prev => ({ ...prev, [nombre]: archivo }))
  }

  // Función para subir un archivo al servidor
  const handleUpload = async (nombre) => {
    const archivo = archivos[nombre]
    if (!archivo) {
      setMensaje("⚠️ Selecciona un archivo antes de subir.")
      return
    }

    // Preparar los datos del formulario
    const formData = new FormData()
    formData.append("archivo", archivo)
    formData.append("nombre_documento", nombre)

    // Enviar la solicitud al servidor
    const res = await fetch(`/api/alumno/${id}/subir`, {
      method: "POST",
      body: formData
    })

    const data = await res.json()

    if (res.ok) {
      setMensaje("✅ Documento subido correctamente.")
      // Recargar la lista de documentos después de subir
      const nuevos = await fetch(`/api/alumno/${id}/documentos`).then(r => r.json())
      setDocumentos(nuevos.documentos)
    } else {
      setMensaje(`❌ Error: ${data.error || "algo salió mal."}`)
    }
  }

  return (
    <div className="min-h-screen bg-green-50 p-6">
      {/* Título del panel */}
      <h1 className="text-3xl font-bold text-green-700 mb-6">
        Panel del Alumno #{id}
      </h1>

      {/* Mostrar mensajes de estado */}
      {mensaje && <p className="mb-4">{mensaje}</p>}

      {/* Lista de documentos */}
      {documentos.map((doc) => (
        <div key={doc.nombre} className="bg-white p-4 rounded-lg shadow mb-4">
          <h2 className="text-xl font-semibold">{doc.nombre}</h2>
          <p>
            Estado:{" "}
            {doc.estado === "subido" && "📄 Subido"}
            {doc.estado === "aceptado" && "✅ Aceptado"}
            {doc.estado === "rechazado" && "❌ Rechazado"}
            {doc.estado === "no_subido" && "⚠️ No subido"}
          </p>

          {/* Sección de acciones para documentos subidos */}
          {doc.subido && (
            <div className="flex items-center space-x-4 mt-2">
              <a
                href={`/descargar_documento/${doc.id}`}
                className="text-blue-600 underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                📥 Descargar
              </a>

              <button
                onClick={async () => {
                  const res = await fetch(`/api/alumno/${id}/documentos/${doc.id}/eliminar`, {
                    method: "DELETE"
                  })
                  const data = await res.json()
                  if (res.ok) {
                    const nuevos = await fetch(`/api/alumno/${id}/documentos`).then(r => r.json())
                    setDocumentos(nuevos.documentos)
                    setMensaje("🗑️ Documento eliminado.")
                  } else {
                    setMensaje(`❌ Error: ${data.error || "no se pudo eliminar."}`)
                  }
                }}
                className="text-red-600 underline"
              >
                Eliminar documento
              </button>
            </div>
          )}

          {/* Input para seleccionar archivo */}
          <input
            type="file"
            onChange={(e) => handleFileChange(doc.nombre, e.target.files[0])}
            className="mt-2"
          />

          {/* Botón para subir el documento */}
          <button
            onClick={() => handleUpload(doc.nombre)}
            className="bg-green-600 text-white px-4 py-1 rounded mt-2 hover:bg-green-700"
          >
            Subir documento
          </button>
        </div>
      ))}
    </div>
  )
}

export default AlumnoPanel