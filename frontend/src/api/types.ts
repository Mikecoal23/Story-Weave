// Shapes mirror backend/app/schemas and backend/app/models/entities.py

// `pin` is not in the backend yet (PIN routes are Sprint 3), so it stays mock-only
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
  theme: string
  lines: string[]
}

// Backend word statuses; the UI's neutral/correct/retry mapping is Open Question 14
export type WordScore = {
  expected_word: string
  recognized_word: string | null
  status: 'mastered' | 'shaky' | 'missed'
}

export type ScoreResult = {
  words: WordScore[]
}

// Response from POST /sessions/{session_id}/lines/{line_number}/audio
export type LineAudioResponse = {
  status: 'complete'
  result: ScoreResult | null
}

// What the parent dashboard shows for one child. The backend has not defined this
// response yet, so this shape is a frontend proposal built from what the UI displays.
export type Dashboard = {
  sessions: number // reading sessions this week
  minutes: number
  lastStory: string
  workingOn: string[] // pattern labels, e.g. ['sh', 'ch']
  strongest: string // pattern to praise
  patterns: { label: string; fill: number }[] // fill is percent mastered
  tryAtHome: string[] // practice words
}
