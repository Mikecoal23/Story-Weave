import { USE_MOCKS } from './config'
import { delay, request } from './client'
import type { Dashboard } from './types'

// Keyed by the fixture child ids (Mia, Leo) from backend/scripts/dev_fixtures.py
const MIA_ID = 'f1000000-0000-4000-8000-0000000000a1'
const LEO_ID = 'f1000000-0000-4000-8000-0000000000a2'

const mockDashboards: Record<string, Dashboard> = {
  [MIA_ID]: {
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
  [LEO_ID]: {
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
    return mockDashboards[childId] ?? mockDashboards[MIA_ID]
  }
  return request<Dashboard>(`/caregivers/${childId}/dashboard`)
}
