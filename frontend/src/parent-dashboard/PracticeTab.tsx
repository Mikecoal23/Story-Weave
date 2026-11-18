import { useState } from 'react'
import { lookupWord, type DictionaryEntry } from '../api/dictionary'
import type { Dashboard } from '../api/types'

type Props = {
  dashboard: Dashboard
}

const TIP = 'Say each word slowly together, then let your child try it alone.'

// The word the parent clicked (and which card it was in); no entry and no error means it is still loading
type Lookup = { sound: string; word: string; entry?: DictionaryEntry; error?: boolean }

function PracticeTab({ dashboard }: Props) {
  const [done, setDone] = useState<string[]>([])
  const [lookup, setLookup] = useState<Lookup | null>(null)

  // One card per pattern the child is working on, with the practice words spelled with it.
  // Patterns with no matching words (e.g. "a_e (silent-e)") are left out.
  const activities = dashboard.working_on
    .map((sound) => ({
      sound,
      words: dashboard.try_at_home.filter((word) => word.toLowerCase().includes(sound.toLowerCase())),
    }))
    .filter((a) => a.words.length > 0)

  function toggle(sound: string) {
    setDone(done.includes(sound) ? done.filter((s) => s !== sound) : [...done, sound])
  }

  function isSelected(sound: string, word: string) {
    return lookup?.sound === sound && lookup.word === word
  }

  async function showWord(sound: string, word: string) {
    setLookup({ sound, word })
    // Only keep the answer if this word is still the one selected (a slow reply could arrive after another click)
    try {
      const entry = await lookupWord(word)
      setLookup((current) =>
        current?.sound === sound && current.word === word ? { sound, word, entry } : current,
      )
    } catch {
      setLookup((current) =>
        current?.sound === sound && current.word === word ? { sound, word, error: true } : current,
      )
    }
  }

  const audioUrl = lookup?.entry?.audio_url

  return (
    <section>
      <h1 className="pd-title">Practice at home</h1>
      {activities.length === 0 ? (
        <div className="pd-note">Nothing to practice yet. Words show up here after a few stories.</div>
      ) : (
        <div className="pd-practice-list">
          {activities.map((a) => (
            <div key={a.sound} className="pd-card">
              <h2 className="pd-heading">Sound: {a.sound}</h2>
              <div className="pd-chips">
                {a.words.map((word) => (
                  <button
                    key={word}
                    type="button"
                    className="pd-chip"
                    aria-pressed={isSelected(a.sound, word)}
                    onClick={() => showWord(a.sound, word)}
                  >
                    {word}
                  </button>
                ))}
              </div>
              {lookup?.sound === a.sound && (
                <div className="pd-definition" aria-live="polite">
                  {lookup.entry ? (
                    <>
                      <p className="pd-stat">
                        <strong>{lookup.entry.word}</strong>
                        {lookup.entry.phonetic && ` (${lookup.entry.phonetic})`}: {lookup.entry.definition}
                      </p>
                      {audioUrl && (
                        <button
                          type="button"
                          className="pd-chip"
                          // play() fails quietly if the browser blocks the sound
                          onClick={() => new Audio(audioUrl).play().catch(() => {})}
                        >
                          🔊 Listen
                        </button>
                      )}
                    </>
                  ) : (
                    <p className="pd-stat">{lookup.error ? "Couldn't find that word." : 'Looking up…'}</p>
                  )}
                </div>
              )}
              <p className="pd-hint">{TIP}</p>
              <button type="button" className="pd-chip" onClick={() => toggle(a.sound)}>
                {done.includes(a.sound) ? '✓ Practiced' : 'Mark as practiced'}
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default PracticeTab
