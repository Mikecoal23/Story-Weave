import { Fragment, useCallback, useEffect, useRef, useState } from 'react'
import { lookupWord, type DictionaryEntry } from '../api/dictionary'
import type { WordScore } from '../api/types'

type Props = {
  line: string
  scores: WordScore[] | null // null until the line has been read and scored
}

// How a scored word looks to the child (Open Question 14): mastered words turn mint
// ("read well"), shaky and missed words turn coral ("try again").
function colorClass(score: WordScore | undefined) {
  if (!score) return ''
  return score.status === 'mastered' ? ' correct' : ' retry'
}

// The backend scores the line split on spaces, so word i lines up with scores[i]
function SentenceReader({ line, scores }: Props) {
  const [selectedWord, setSelectedWord] = useState<string | null>(null)
  const [entry, setEntry] = useState<DictionaryEntry | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const latestLookup = useRef(0)

  const showWord = useCallback(async (word: string) => {
    const lookupId = ++latestLookup.current
    const cleanWord = word.replace(/^[^A-Za-z]+|[^A-Za-z]+$/g, '')
    if (!cleanWord) return

    setSelectedWord(word)
    setEntry(null)
    setError('')
    setLoading(true)
    try {
      const result = await lookupWord(cleanWord)
      if (lookupId === latestLookup.current) setEntry(result)
    } catch {
      if (lookupId === latestLookup.current) {
        setError("We couldn't find that word right now. Please try again.")
      }
    } finally {
      if (lookupId === latestLookup.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    const firstUnmastered = scores?.find((score) => score.status !== 'mastered')
    const timer = window.setTimeout(() => {
      if (firstUnmastered) {
        void showWord(firstUnmastered.expected_word)
        return
      }
      latestLookup.current += 1
      setSelectedWord(null)
      setEntry(null)
      setError('')
      setLoading(false)
    }, 0)
    return () => {
      window.clearTimeout(timer)
      latestLookup.current += 1
    }
  }, [scores, showWord])

  return (
    <section className="reader">
      <h2 className="prompt">Read this sentence</h2>
      <p className="sentence">
        {line.split(' ').map((word, i) => (
          <Fragment key={i}>
            {i > 0 && ' '}
            <button
              aria-label={`Look up ${word}`}
              aria-pressed={selectedWord === word}
              className={`word${colorClass(scores?.[i])}${selectedWord === word ? ' selected' : ''}`}
              onClick={() => void showWord(scores?.[i]?.expected_word ?? word)}
              type="button"
            >
              {word}
            </button>
          </Fragment>
        ))}
      </p>
      {selectedWord && (
        <aside aria-live="polite" className="word-definition">
          <div className="definition-heading">
            <h3>{entry?.word ?? selectedWord.replace(/^[^A-Za-z]+|[^A-Za-z]+$/g, '')}</h3>
            {entry?.phonetic && <span className="phonetic">/{entry.phonetic}/</span>}
            <button
              aria-label={`Play pronunciation for ${entry?.word ?? selectedWord}`}
              className="play-pronunciation"
              disabled={!entry?.audio_url}
              onClick={() => {
                if (entry?.audio_url) {
                  void new Audio(entry.audio_url)
                    .play()
                    .catch(() => setError("Audio playback isn't available right now."))
                }
              }}
              type="button"
            >
              Hear word
            </button>
          </div>
          {loading && <p>Looking up the word…</p>}
          {error && <p role="alert">{error}</p>}
          {entry && <p className="definition-text">{entry.definition}</p>}
        </aside>
      )}
    </section>
  )
}

export default SentenceReader
