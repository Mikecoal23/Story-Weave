import { USE_MOCKS } from './config'
import { children } from '../parent-dashboard/mockChildren'
import type { Child } from './types'

// No GET children route exists yet, so this always returns the mock list.
// A copy, so callers holding it in state see a new array after a child is added.
export async function getChildren(): Promise<Child[]> {
  return [...children]
}

export async function createChild(data: Pick<Child, 'name' | 'interests' | 'gradeLevel'>): Promise<Child> {
  if (USE_MOCKS.children) {
    const child: Child = { ...data, id: crypto.randomUUID(), pin: '1234' }
    children.push(child)
    return child
  }
  throw new Error('POST /children request body is not defined by the backend yet')
}
