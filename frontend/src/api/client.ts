import { API_URL } from './config'

// Waits, so mock functions can pretend to be a network call
export function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Small wrapper around fetch: adds the base URL, reads JSON, throws on errors
// (this includes the backend's 501 "Not implemented yet" stubs).
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // File uploads (FormData) must not get a JSON Content-Type; the browser sets its own
  const headers: HeadersInit =
    init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { ...headers, ...init?.headers },
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}
