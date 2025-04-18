import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function LoginAlumno() {
  const [credencial, setCredencial] = useState('')
  const [mensaje, setMensaje] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/login_alumno`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credencial })
      })
    

      const data = await res.json()

      if (!res.ok) {
        localStorage.removeItem("token_alumno")
        setMensaje("❌ Credenciales incorrectas")
        return
      }
      

      localStorage.setItem("token_alumno", data.token)
      navigate(`/alumno/${data.alumno_id}`)

    } catch (err) {
      console.error("Error al conectar:", err)
      setMensaje("⚠️ Error de red")
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-green-100">
      <div className="w-full max-w-md p-8 shadow-lg rounded-2xl bg-white border border-gray-200">
        <h2 className="text-2xl font-bold mb-6 text-center text-green-700">
          Acceso de Alumnos
        </h2>

        {mensaje && <p className="mb-4 text-red-600 text-center">{mensaje}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Nombre y apellidos"
            value={credencial}
            onChange={(e) => setCredencial(e.target.value)}
            className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-400"
            required
          />
          <button
            type="submit"
            className="w-full py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition font-semibold"
          >
            Entrar
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginAlumno