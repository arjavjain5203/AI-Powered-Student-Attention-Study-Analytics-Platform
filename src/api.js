const base = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export async function api(path, { token, method = 'GET', body, signal } = {}) {
  const response = await fetch(`${base}${path}`, {
    method,
    headers: { ...(body && !(body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    ...(body ? { body: body instanceof FormData ? body : JSON.stringify(body) } : {}),
    ...(signal ? { signal } : {}),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status})`)
    error.status = response.status
    throw error
  }
  return data
}
