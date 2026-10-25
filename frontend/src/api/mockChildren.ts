import type { Child } from './types'

// Sample children for when USE_MOCKS.children is true; read through api/children.ts.
// Same ids as the fixture children in backend/scripts/dev_fixtures.py.
export const children: Child[] = [
  { id: 'f1000000-0000-4000-8000-0000000000a1', name: 'Mia', interests: ['dinosaurs', 'the ocean'], gradeLevel: 1, pin: '1234' },
  { id: 'f1000000-0000-4000-8000-0000000000a2', name: 'Leo', interests: ['trucks', 'space'], gradeLevel: 1, pin: '1234' },
]
