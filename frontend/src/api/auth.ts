const BASE = '/api/v1/auth'

export interface AuthUser {
  user_id: string
  username: string
  created_at: string | null
}

async function handleResponse(res: Response): Promise<any> {
  if (!res.ok) {
    let detail = 'Request failed'
    try {
      const err = await res.json()
      if (typeof err.detail === 'string') {
        detail = err.detail
      } else if (Array.isArray(err.detail)) {
        // FastAPI validation errors: [{loc, msg, type}]
        detail = err.detail.map((d: any) => d.msg).filter(Boolean).join('; ') || 'Validation failed'
      } else if (err.detail && typeof err.detail === 'object') {
        detail = JSON.stringify(err.detail)
      } else if (err.error) {
        detail = String(err.error)
      } else {
        detail = JSON.stringify(err)
      }
    } catch {}
    throw new Error(detail)
  }
  return res.json()
}

export async function register(username: string, password: string) {
  const res = await fetch(BASE + '/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  return handleResponse(res)
}

export async function login(username: string, password: string) {
  const res = await fetch(BASE + '/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  return handleResponse(res)
}

export async function refresh(token: string) {
  const res = await fetch(BASE + '/refresh', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  return handleResponse(res)
}

export async function me(token: string): Promise<AuthUser> {
  const res = await fetch(BASE + '/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
  return handleResponse(res)
}
