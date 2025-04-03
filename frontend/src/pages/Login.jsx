import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Login({ tipo = 'admin' }) {
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const esAdmin = tipo === 'admin'

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      if (esAdmin) {
        const res = await fetch("http://localhost:5001/api/login_jwt", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ usuario, contrasena: password })
        })

        const data = await res.json()

        if (res.ok && data.token) {
          localStorage.setItem("token", data.token)
          const decoded = JSON.parse(atob(data.token.split('.')[1]))
          navigate(decoded.es_superadmin ? "/superadmin" : "/admin")
        } else {
          alert(`❌ ${data.error || "Credenciales incorrectas"}`)
        }
      } else {
        const res = await fetch("http://localhost:5001/api/login_alumno", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ credencial: usuario })
        })

        const data = await res.json()
        if (res.ok) {
          navigate(`/alumno/${data.alumno_id}`)
        } else {
          alert(`❌ ${data.error || "Credencial incorrecta"}`)
        }
      }
    } catch (err) {
      console.error(err)
      alert("⚠️ Error al conectar con el servidor")
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
            placeholder={esAdmin ? "Usuario" : "Nombre y apellidos"}
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            required
          />
          {esAdmin && (
            <input
              type="password"
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
              required
            />
          )}
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

