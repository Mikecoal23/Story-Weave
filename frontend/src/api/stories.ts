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

// _childId is unused by the mock but kept so the signature matches the real route
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function generateStory(_childId: string): Promise<Story> {
  if (USE_MOCKS.stories) {
    await delay(2000) // same wait as the old LoadingScreen timer
    return mockStory
  }
  throw new Error('POST /stories/generate request body is not defined by the backend yet')
}

export async function getStory(id: string): Promise<Story> {
  if (USE_MOCKS.stories) return mockStory
  return request<Story>(`/stories/${id}`)
}
