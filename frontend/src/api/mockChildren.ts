import type { Child } from './types'

// Static sample data until GET /children is connected; read through api/children.ts
export const children: Child[] = [
  { id: '701df406-cebb-43be-b59b-79c50fd343f0', name: 'Mia', interests: ['dinosaurs', 'the ocean'], gradeLevel: 1, pin: '1234' },
  { id: '2', name: 'Leo', interests: ['trucks', 'space'], gradeLevel: 1, pin: '1234' },
]
