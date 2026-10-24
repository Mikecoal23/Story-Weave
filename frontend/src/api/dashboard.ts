import { USE_MOCKS } from './config'
import { delay, request } from './client'
import type { Dashboard } from './types'

const mockDashboards: Record<string, Dashboard> = {
  '1': {
    sessions: 3,
    minutes: 12,
    lastStory: 'The Shell on the Beach',
    workingOn: ['sh', 'ch'],
    strongest: 'silent-e',
    patterns: [
      { label: 'sh', fill: 90 },
      { label: 'ch', fill: 65 },
      { label: 'blends', fill: 30 },
    ],
    tryAtHome: ['shop', 'shell', 'shed'],
  },
  '2': {
    sessions: 5,
    minutes: 20,
    lastStory: 'The Truck on the Moon',
    workingOn: ['th', 'blends'],
    strongest: 'sh',
    patterns: [
      { label: 'th', fill: 55 },
      { label: 'blends', fill: 40 },
      { label: 'sh', fill: 85 },
    ],
    tryAtHome: ['this', 'that', 'frog'],
  },
}

export async function getDashboard(childId: string): Promise<Dashboard> {
  if (USE_MOCKS.dashboard) {
    await delay(300)
    // Children added in the app have no sample data, so they fall back to the first one
    return mockDashboards[childId] ?? mockDashboards['1']
  }
  return request<Dashboard>(`/caregivers/${childId}/dashboard`)
}
