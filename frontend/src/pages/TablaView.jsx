import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Login({ tipo = 'alumno' }) {
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const esAdmin = tipo === 'admin'
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()

    const endpoint = tipo === 'admin' ? '/' : '/login_alumno'

    try {
      const res = await fetch(`http://localhost:5001${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // ✅ NECESARIO
        body: JSON.stringify({ usuario, contrasena: password }),
      })

      const data = await res.json()

      if (res.ok) {
        if (tipo === 'admin') {
          if (data.es_superadmin) {
            navigate('/superadmin')
          } else {
            navigate('/admin')
          }
        } else {
          navigate(`/alumno/${usuario}`)
        }
      } else {
        alert('❌ Credenciales incorrectas')
      }
    } catch (error) {
      alert('⚠️ Error al conectar con el servidor')
      console.error(error)
    }
  }

  return (
    <div className={`min-h-screen flex items-center justify-center ${esAdmin ? 'bg-blue-100' : 'bg-gray-50'}`}>
      <div className="w-full max-w-md p-8 shadow-lg rounded-2xl bg-white border border-gray-200">
        <h2 className={`text-2xl font-bold mb-6 text-center ${esAdmin ? 'text-blue-800' : 'text-gray-800'}`}>
          Iniciar sesión como {esAdmin ? 'Administrador' : 'Alumno'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Usuario"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            required
          />
          <input
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            required
          />
          <button
            type="submit"
            className={`w-full py-2 rounded-md text-white font-semibold transition ${
              esAdmin ? 'bg-blue-700 hover:bg-blue-800' : 'bg-blue-500 hover:bg-blue-600'
            }`}
          >
            Entrar
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
