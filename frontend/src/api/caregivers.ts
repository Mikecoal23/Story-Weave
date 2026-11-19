import { request, setSessionToken } from './client'

// The logged-in caregiver, set by login(). Kept in sessionStorage so a refresh stays logged in;
// closing the tab clears it.
let caregiverId = sessionStorage.getItem('caregiverId') ?? ''
let caregiverPinSet = sessionStorage.getItem('caregiverPinSet') === 'true'
// Remembered so "Forgot PIN?" can check the parent knows the account email
let caregiverEmail = sessionStorage.getItem('caregiverEmail') ?? ''

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

// Ignores case and extra spaces, so " Mom@Example.com" still matches
export function emailMatches(email: string) {
  return caregiverEmail !== '' && email.trim().toLowerCase() === caregiverEmail
}

export function logout() {
  caregiverId = ''
  caregiverPinSet = false
  caregiverEmail = ''
  sessionStorage.removeItem('caregiverId')
  sessionStorage.removeItem('caregiverPinSet')
  sessionStorage.removeItem('caregiverEmail')
  setSessionToken('')
}

// Shared by login() and createAccount(): remember the caregiver in memory and in sessionStorage
function saveSession(session: CaregiverSession, email: string) {
  caregiverId = session.caregiver_id
  caregiverPinSet = session.pin_set
  caregiverEmail = email.trim().toLowerCase()
  sessionStorage.setItem('caregiverId', caregiverId)
  sessionStorage.setItem('caregiverPinSet', String(caregiverPinSet))
  sessionStorage.setItem('caregiverEmail', caregiverEmail)
  setSessionToken(session.token)
}

// No password: the backend finds the caregiver by email (planning.md, Open Question 12)
export async function login(email: string) {
  const session = await request<CaregiverSession>('/caregivers/session', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
  saveSession(session, email)
}

// Creates the caregiver and logs them in; the backend returns a session either way
export async function createAccount(name: string, email: string, pin: string) {
  const session = await request<CaregiverSession>('/caregivers', {
    method: 'POST',
    body: JSON.stringify({ display_name: name, email, pin }),
  })
  saveSession(session, email)
}

export async function setCaregiverPin(pin: string): Promise<void> {
  await request<void>(`/caregivers/${caregiverId}/pin`, {
    method: 'PUT',
    body: JSON.stringify({ pin }),
  })
  caregiverPinSet = true
  sessionStorage.setItem('caregiverPinSet', 'true')
}

export async function verifyCaregiverPin(pin: string): Promise<boolean> {
  const result = await request<{ verified: boolean }>(
    `/caregivers/${caregiverId}/verify-pin`,
    { method: 'POST', body: JSON.stringify({ pin }) },
  )
  return result.verified
}
