export type Child = { id: number; name: string; interests: string[]; pin: string }

// Static sample data until GET /children is connected
export const children: Child[] = [
  { id: 1, name: 'Mia', interests: ['dinosaurs', 'the ocean'], pin: '1234' },
  { id: 2, name: 'Leo', interests: ['trucks', 'space'], pin: '1234' },
]
