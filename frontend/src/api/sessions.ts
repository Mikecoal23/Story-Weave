import { request } from './client'
import type { LineAudioResponse } from './types'

export async function startSession(childId: string, storyId: string): Promise<{ id: string }> {
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
  // The backend expects a multipart form with the recording in a field named "audio"
  const form = new FormData()
  form.append('audio', audio)
  return request<LineAudioResponse>(`/sessions/${sessionId}/lines/${lineNumber}/audio`, {
    method: 'POST',
    body: form,
  })
}
