import { getCaregiverId } from './caregivers'
import { request } from './client'
import type { Child } from './types'

// A child as the backend sends it (backend ChildResponse)
type ApiChild = {
  id: string
  display_name: string
  grade_level: number
  interests: string[]
}

// Backend names -> frontend names, so the rest of the UI keeps using `name` and `gradeLevel`.
// `pin` is not in the backend yet, so it is filled in here.
function fromApi(c: ApiChild): Child {
  return {
    id: c.id,
    name: c.display_name,
    gradeLevel: c.grade_level,
    interests: c.interests,
    pin: '1234',
  }
}

export async function getChildren(): Promise<Child[]> {
  const list = await request<ApiChild[]>(`/caregivers/${getCaregiverId()}/children`)
  return list.map(fromApi)
}

export async function createChild(data: Pick<Child, 'name' | 'interests' | 'gradeLevel'>): Promise<Child> {
  // Frontend names -> backend names
  const created = await request<ApiChild>('/children', {
    method: 'POST',
    body: JSON.stringify({
      caregiver_id: getCaregiverId(),
      display_name: data.name,
      grade_level: data.gradeLevel,
      interests: data.interests,
    }),
  })
  return fromApi(created)
}

// Also deletes the child's stories, sessions and progress (the backend cascades)
export async function deleteChild(id: string): Promise<void> {
  await request<void>(`/children/${id}`, { method: 'DELETE' })
}
