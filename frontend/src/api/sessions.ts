import { USE_MOCKS } from './config'
import { delay, request } from './client'
import type { LineAudioResponse } from './types'

export async function startSession(childId: string, storyId: string): Promise<{ id: string }> {
  if (USE_MOCKS.sessions) return { id: 'mock-session-1' }
  return request<{ id: string }>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ child_id: childId, story_id: storyId }),
  })
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
