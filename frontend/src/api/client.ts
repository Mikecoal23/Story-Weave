import { API_URL } from './config'

// Small wrapper around fetch: adds the base URL, reads JSON, throws on non-2xx responses
let sessionToken = ''

export function setSessionToken(token: string) {
  sessionToken = token
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // File uploads (FormData) must not get a JSON Content-Type; the browser sets its own
  const headers: HeadersInit =
    init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }
  const requestHeaders = new Headers(headers)
  if (sessionToken) requestHeaders.set('Authorization', `Bearer ${sessionToken}`)
  new Headers(init?.headers).forEach((value, key) => requestHeaders.set(key, value))
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: requestHeaders,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  // 204 No Content (e.g. a delete) has no body, so there is no JSON to read
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}
