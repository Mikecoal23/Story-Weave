import { API_URL } from './config'

// Small wrapper around fetch: adds the base URL, reads JSON, throws on non-2xx responses
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // File uploads (FormData) must not get a JSON Content-Type; the browser sets its own
  const headers: HeadersInit =
    init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { ...headers, ...init?.headers },
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  // 204 No Content (e.g. a delete) has no body, so there is no JSON to read
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}
