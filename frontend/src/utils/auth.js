// src/utils/auth.js
export function requireAuth() {
  const token = localStorage.getItem('token')
  if (!token) return null

  try {
    const payload = JSON.parse(atob(token.split('.')[1])) // decode base64
    return payload
  } catch (err) {
    console.error("Token no válido:", err)
    return null
  }
}
