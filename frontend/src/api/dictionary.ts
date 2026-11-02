import { request } from './client'

export type DictionaryEntry = {
  word: string
  phonetic: string | null
  definition: string
  audio_url: string | null
}

export function lookupWord(word: string): Promise<DictionaryEntry> {
  return request<DictionaryEntry>(`/dictionary/${encodeURIComponent(word)}`)
}
