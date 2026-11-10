import { USE_MOCKS } from './config'
import { delay, request } from './client'
import type { Dashboard } from './types'

// Keyed by the fixture child ids (Mia, Leo) from backend/scripts/dev_fixtures.py
const MIA_ID = 'f1000000-0000-4000-8000-0000000000a1'
const LEO_ID = 'f1000000-0000-4000-8000-0000000000a2'

const mockDashboards: Record<string, Dashboard> = {
  [MIA_ID]: {
    sessions: 3,
    last_story: 'The Shell on the Beach',
    working_on: ['sh', 'ch'],
    strongest: 'silent-e',
    patterns: [
      { label: 'sh', fill: 90 },
      { label: 'ch', fill: 65 },
      { label: 'blends', fill: 30 },
    ],
    try_at_home: ['shop', 'shell', 'shed'],
  },
  [LEO_ID]: {
    sessions: 5,
    last_story: 'The Truck on the Moon',
    working_on: ['th', 'blends'],
    strongest: 'sh',
    patterns: [
      { label: 'th', fill: 55 },
      { label: 'blends', fill: 40 },
      { label: 'sh', fill: 85 },
    ],
    try_at_home: ['this', 'that', 'frog'],
  },
}

const emptyDashboard: Dashboard = {
  sessions: 0,
  last_story: null,
  working_on: [],
  strongest: null,
  patterns: [],
  try_at_home: [],
}

export async function getDashboard(childId: string): Promise<Dashboard> {
  if (USE_MOCKS.dashboard) {
    await delay(300)
    // Children added in the app have no sessions yet
    return mockDashboards[childId] ?? emptyDashboard
  }
  return request<Dashboard>(`/children/${childId}/dashboard`)
}
