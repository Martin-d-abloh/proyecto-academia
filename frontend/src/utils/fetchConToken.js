// src/utils/fetchConToken.js

export async function fetchConToken(url, options = {}) {
  const token = localStorage.getItem("token")

  const headers = {
    ...(options.headers || {}),
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  }

  const config = {
    ...options,
    headers,
  }

  return fetch(url, config)
}
