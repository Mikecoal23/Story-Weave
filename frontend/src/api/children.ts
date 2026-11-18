import { getCaregiverId } from './caregivers'
import { request } from './client'
import type { Child } from './types'

// A child as the backend sends it (backend ChildResponse)
type ApiChild = {
  id: string
  display_name: string
  grade_level: number
  interests: string[]
  pin_set: boolean
}

// Backend names -> frontend names, so the rest of the UI keeps using `name` and `gradeLevel`.
function fromApi(c: ApiChild): Child {
  return {
    id: c.id,
    name: c.display_name,
    gradeLevel: c.grade_level,
    interests: c.interests,
    pinSet: c.pin_set,
  }
}

export async function getChildren(): Promise<Child[]> {
  const list = await request<ApiChild[]>(`/caregivers/${getCaregiverId()}/children`)
  return list.map(fromApi)
}

export async function createChild(
  data: Pick<Child, 'name' | 'interests' | 'gradeLevel'> & { pin: string },
): Promise<Child> {
  // Frontend names -> backend names
  const created = await request<ApiChild>('/children', {
    method: 'POST',
    body: JSON.stringify({
      caregiver_id: getCaregiverId(),
      display_name: data.name,
      grade_level: data.gradeLevel,
      interests: data.interests,
      pin: data.pin,
    }),
  })
  return fromApi(created)
}

export async function verifyChildPin(id: string, pin: string): Promise<boolean> {
  const result = await request<{ verified: boolean }>(`/children/${id}/verify-pin`, {
    method: 'POST',
    body: JSON.stringify({ pin }),
  })
  return result.verified
}

export async function getChildPin(id: string): Promise<string> {
  const result = await request<{ pin: string }>(`/children/${id}/pin`)
  return result.pin
}

export async function setChildPin(id: string, pin: string): Promise<void> {
  await request<void>(`/children/${id}/pin`, {
    method: 'PUT',
    body: JSON.stringify({ pin }),
  })
}

// Also deletes the child's stories, sessions and progress (the backend cascades)
export async function deleteChild(id: string): Promise<void> {
  await request<void>(`/children/${id}`, { method: 'DELETE' })
}
