import { request } from './client'
import type { Dashboard } from './types'

export async function getDashboard(childId: string): Promise<Dashboard> {
  return request<Dashboard>(`/children/${childId}/dashboard`)
}
