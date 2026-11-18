import { request, setSessionToken } from './client'

// The logged-in caregiver's id, set by login(). Lives only in memory, so a page refresh logs out.
let caregiverId = ''
let caregiverPinSet = false

type CaregiverSession = {
  caregiver_id: string
  token: string
  pin_set: boolean
}

export function getCaregiverId() {
  return caregiverId
}

export function hasCaregiverPin() {
  return caregiverPinSet
}

export function logout() {
  caregiverId = ''
  caregiverPinSet = false
  setSessionToken('')
}

// No password: the backend finds the caregiver by email (planning.md, Open Question 12)
export async function login(email: string) {
  const session = await request<CaregiverSession>('/caregivers/session', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
  caregiverId = session.caregiver_id
  caregiverPinSet = session.pin_set
  setSessionToken(session.token)
}

// Creates the caregiver and logs them in; the backend returns a session either way
export async function createAccount(name: string, email: string, pin: string) {
  const session = await request<CaregiverSession>('/caregivers', {
    method: 'POST',
    body: JSON.stringify({ display_name: name, email, pin }),
  })
  caregiverId = session.caregiver_id
  caregiverPinSet = session.pin_set
  setSessionToken(session.token)
}

export async function setCaregiverPin(pin: string): Promise<void> {
  await request<void>(`/caregivers/${caregiverId}/pin`, {
    method: 'PUT',
    body: JSON.stringify({ pin }),
  })
  caregiverPinSet = true
}

export async function verifyCaregiverPin(pin: string): Promise<boolean> {
  const result = await request<{ verified: boolean }>(
    `/caregivers/${caregiverId}/verify-pin`,
    { method: 'POST', body: JSON.stringify({ pin }) },
  )
  return result.verified
}
