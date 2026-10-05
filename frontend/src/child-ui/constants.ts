import type { WordStatus } from './types'

export const words: { text: string; status: WordStatus }[] = [
  { text: 'The', status: 'neutral' },
  { text: 'ship', status: 'correct' },
  { text: 'sank', status: 'correct' },
  { text: 'in', status: 'neutral' },
  { text: 'the', status: 'neutral' },
  { text: 'shell', status: 'retry' },
  { text: 'shop.', status: 'neutral' },
]
