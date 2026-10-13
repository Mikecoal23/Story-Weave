import { useState } from 'react'

// Static sample data until the dashboard endpoint is connected
const activities = [
  { sound: 'sh', words: ['shop', 'shell', 'shed'], tip: 'Say the word slowly, then have your child copy the "sh" sound.' },
  { sound: 'ch', words: ['chip', 'chop', 'chin'], tip: 'Find things around the house that start with "ch".' },
  { sound: 'th', words: ['this', 'that', 'thin'], tip: 'Show how the tongue touches the teeth for "th".' },
]

function PracticeTab() {
  const [done, setDone] = useState<string[]>([])

  function toggle(sound: string) {
    setDone(done.includes(sound) ? done.filter((s) => s !== sound) : [...done, sound])
  }

  return (
    <section>
      <h1 className="pd-title">Practice at home</h1>
      <div className="pd-practice-list">
        {activities.map((a) => (
          <div key={a.sound} className="pd-card">
            <h2 className="pd-heading">Sound: {a.sound}</h2>
            <div className="pd-chips">
              {a.words.map((word) => (
                <span key={word} className="pd-chip">
                  {word}
                </span>
              ))}
            </div>
            <p className="pd-hint">{a.tip}</p>
            <button type="button" className="pd-chip" onClick={() => toggle(a.sound)}>
              {done.includes(a.sound) ? '✓ Practiced' : 'Mark as practiced'}
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}

export default PracticeTab
