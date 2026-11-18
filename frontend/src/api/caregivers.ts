import { request } from './client'

// The logged-in caregiver's id, set by login(). Also saved in localStorage so a page refresh keeps you logged in.
const STORAGE_KEY = 'caregiverId'
let caregiverId = localStorage.getItem(STORAGE_KEY) ?? ''

function setCaregiverId(id: string) {
  caregiverId = id
  localStorage.setItem(STORAGE_KEY, id)
}

export function getCaregiverId() {
  return caregiverId
}

export function logout() {
  caregiverId = ''
  localStorage.removeItem(STORAGE_KEY)
}

// No password: the backend finds the caregiver by email (planning.md, Open Question 12)
export async function login(email: string) {
  const session = await request<{ caregiver_id: string }>('/caregivers/session', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
  setCaregiverId(session.caregiver_id)
}

// Creates the caregiver and logs them in; the backend returns a session either way
export async function createAccount(name: string, email: string) {
  const session = await request<{ caregiver_id: string }>('/caregivers', {
    method: 'POST',
    body: JSON.stringify({ display_name: name, email }),
  })
  setCaregiverId(session.caregiver_id)
}
