import { USE_MOCKS } from './config'
import { delay, request } from './client'
import type { LineAudioResponse } from './types'

// Underscored params are unused by the mock but match the real route's needs
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function startSession(_childId: string, _storyId: string): Promise<{ id: string }> {
  if (USE_MOCKS.sessions) return { id: 'mock-session-1' }
  throw new Error('POST /sessions request body is not defined by the backend yet')
}

export async function uploadLineAudio(
  sessionId: string,
  lineNumber: number,
  audio: Blob,
): Promise<LineAudioResponse> {
  if (USE_MOCKS.sessions) {
    await delay(500)
    return {
      status: 'complete',
      result: {
        words: [
          { expected_word: 'a', recognized_word: 'a', status: 'mastered' },
          { expected_word: 'ship', recognized_word: 'sip', status: 'shaky' },
          { expected_word: 'sat', recognized_word: null, status: 'missed' },
        ],
      },
    }
  }
  // The backend expects a multipart form with the recording in a field named "audio"
  const form = new FormData()
  form.append('audio', audio)
  return request<LineAudioResponse>(`/sessions/${sessionId}/lines/${lineNumber}/audio`, {
    method: 'POST',
    body: form,
  })
}
