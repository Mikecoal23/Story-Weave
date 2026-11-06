import { request } from './client'

// The logged-in caregiver's id, set by login(). Lives only in memory, so a page refresh logs out.
let caregiverId = ''

export function getCaregiverId() {
  return caregiverId
}

export function logout() {
  caregiverId = ''
}

// No password: the backend finds the caregiver by email (planning.md, Open Question 12)
export async function login(email: string) {
  const session = await request<{ caregiver_id: string }>('/caregivers/session', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
  caregiverId = session.caregiver_id
}

// Creates the caregiver and logs them in; the backend returns a session either way
export async function createAccount(name: string, email: string) {
  const session = await request<{ caregiver_id: string }>('/caregivers', {
    method: 'POST',
    body: JSON.stringify({ display_name: name, email }),
  })
  caregiverId = session.caregiver_id
}
