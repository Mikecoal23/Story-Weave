import { request } from './client'
import type { Story } from './types'

export async function generateStory(childId: string): Promise<Story> {
  return request<Story>('/stories/generate', {
    method: 'POST',
    body: JSON.stringify({ child_id: childId }), // backend expects snake_case
  })
}
