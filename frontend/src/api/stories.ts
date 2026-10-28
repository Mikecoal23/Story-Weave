import { USE_MOCKS } from './config'
import { delay, request } from './client'
import type { Story } from './types'

const mockStory: Story = {
  id: 'a7ecc5f3-59ce-4c69-acc9-20fd817df543',
  title: 'The Ship and the Fish',
  theme: 'the ocean',
  lines: [
    'A ship sat on the bay.',
    'A fish swam by the ship.',
    'The fish had a shiny fin.',
    'The ship and the fish had fun.',
  ],
}

export async function generateStory(childId: string): Promise<Story> {
  if (USE_MOCKS.stories) {
    await delay(2000) // same wait as the old LoadingScreen timer
    return mockStory
  }
  return request<Story>('/stories/generate', {
    method: 'POST',
    body: JSON.stringify({ child_id: childId }), // backend expects snake_case
  })
}
