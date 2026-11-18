import { request } from './client'

// One word from GET /dictionary/{word} (Merriam-Webster student dictionary)
export type DictionaryEntry = {
  word: string
  phonetic: string | null
  definition: string
  audio_url: string | null // mp3 of the word being said, when Merriam-Webster has one
}

export async function lookupWord(word: string): Promise<DictionaryEntry> {
  return request<DictionaryEntry>(`/dictionary/${encodeURIComponent(word)}`)
}
