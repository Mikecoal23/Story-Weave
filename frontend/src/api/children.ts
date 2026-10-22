import { CAREGIVER_ID, USE_MOCKS } from './config'
import { request } from './client'
import { children } from './mockChildren'
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
  if (USE_MOCKS.children) {
    // A copy, so callers holding it in state see a new array after a child is added.
    return [...children]
  }
  const list = await request<ApiChild[]>(`/caregivers/${CAREGIVER_ID}/children`)
  return list.map(fromApi)
}

export async function createChild(data: Pick<Child, 'name' | 'interests' | 'gradeLevel'>): Promise<Child> {
  if (USE_MOCKS.children) {
    const child: Child = { ...data, id: crypto.randomUUID(), pin: '1234' }
    children.push(child)
    return child
  }
  // Frontend names -> backend names
  const created = await request<ApiChild>('/children', {
    method: 'POST',
    body: JSON.stringify({
      caregiver_id: CAREGIVER_ID,
      display_name: data.name,
      grade_level: data.gradeLevel,
      interests: data.interests,
    }),
  })
  return fromApi(created)
}
