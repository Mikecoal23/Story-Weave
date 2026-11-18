// Shapes mirror backend/app/schemas and backend/app/models/entities.py

// `pin` is not in the backend yet (PIN routes wait on Open Question 13); api/children.ts fills in a placeholder
export type Child = {
  id: string // UUID
  name: string // backend field: display_name
  interests: string[]
  gradeLevel: number
  pin: string
}

// Same shape as the backend's DraftStory, plus the id once it is saved
export type Story = {
  id: string
  title: string
  theme: string | null // nullable in the backend's story.theme
  character: string | null // one name from the agreed character list, or null
  lines: string[]
}

// Backend word statuses; SentenceReader.tsx maps them to colors (mastered → mint, shaky/missed → coral)
export type WordScore = {
  expected_word: string
  recognized_word: string | null
  status: 'mastered' | 'shaky' | 'missed'
  error_classification?: 'articulation' | 'unclassified' | null
}

export type ScoreResult = {
  words: WordScore[]
}

// Response from POST /sessions/{session_id}/lines/{line_number}/audio
export type LineAudioResponse = {
  status: 'complete'
  result: ScoreResult | null
}

// What the parent dashboard shows for one child, from GET /children/{child_id}/dashboard.
// snake_case like the backend, so the response is used as it comes (no mapping).
export type Dashboard = {
  sessions: number // reading sessions this week
  last_story: string | null // null until the first session
  working_on: string[] // pattern labels, e.g. ['sh', 'ch']
  strongest: string | null // pattern to praise; null until there is data
  patterns: { label: string; fill: number }[] // fill is percent mastered
  try_at_home: string[] // practice words
}
