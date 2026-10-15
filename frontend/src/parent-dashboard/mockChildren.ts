import type { Child } from '../api/types'

// Static sample data until GET /children is connected; read through api/children.ts
export const children: Child[] = [
  { id: '1', name: 'Mia', interests: ['dinosaurs', 'the ocean'], gradeLevel: 1, pin: '1234' },
  { id: '2', name: 'Leo', interests: ['trucks', 'space'], gradeLevel: 1, pin: '1234' },
]
