import { useParams } from "react-router-dom"

function AlumnoPanel() {
  const { id } = useParams()

  return (
    <div className="min-h-screen flex items-center justify-center bg-green-50">
      <h1 className="text-3xl font-bold text-green-700">
        Bienvenido, Alumno #{id} 📄
      </h1>
    </div>
  )
}

export default AlumnoPanel
