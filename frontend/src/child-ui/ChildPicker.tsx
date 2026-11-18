import './ChildPicker.css'
import type { Child } from '../api/types'

type Props = {
  childList: Child[]
  onSelect: (child: Child) => void
  onBack: () => void // back to "Who's using StoryWeave?"
}

// Interest keyword -> card emoji and color theme. Same emojis and color groups as the reader themes in ChildApp.
const interestLooks: Record<string, [string, string]> = {
  fish: ['🐟', 'ocean'], ship: ['⛵', 'ocean'], ocean: ['🌊', 'ocean'],
  rocket: ['🚀', 'space'], robot: ['🤖', 'space'], space: ['🪐', 'space'],
  frog: ['🐸', 'nature'], bear: ['🐻', 'nature'], bug: ['🐞', 'nature'], dinosaur: ['🦕', 'nature'],
  unicorn: ['🦄', 'magic'], dragon: ['🐉', 'magic'], bird: ['🐦', 'magic'],
  cat: ['🐱', 'cozy'], dog: ['🐶', 'cozy'],
}

// First keyword found inside the interests ("dinosaurs" contains "dinosaur"). No match: a star and the default card color.
function lookFor(interests: string[]) {
  const text = interests.join(' ').toLowerCase()
  const key = Object.keys(interestLooks).find((k) => text.includes(k))
  return key ? interestLooks[key] : ['⭐', 'default']
}

// Used by the child side: pick who is reading, then enter that child's PIN
function ChildPicker({ childList, onSelect, onBack }: Props) {
  return (
    <main className="cp-picker">
      <span className="cp-shape cp-shape-mint" />
      <span className="cp-shape cp-shape-pink" />
      <span className="cp-shape cp-shape-peach" />
      <button type="button" className="cp-back" onClick={onBack}>
        ← Back
      </button>
      <h1 className="cp-title">Who is reading?</h1>
      {childList.length === 0 && (
        <p className="cp-empty">No readers yet. Ask a grown-up to add you in the Parent area.</p>
      )}
      <div className="cp-list">
        {childList.map((c) => {
          const [emoji, theme] = lookFor(c.interests)
          return (
            <button key={c.id} className={`cp-card cp-theme-${theme}`} onClick={() => onSelect(c)}>
              {/* aria-hidden: decoration only, so screen readers skip it */}
              <span className="cp-emoji" aria-hidden="true">{emoji}</span>
              <span className="cp-name">{c.name}</span>
              <span className="cp-likes">Likes: {c.interests.join(', ')}</span>
            </button>
          )
        })}
      </div>
    </main>
  )
}

export default ChildPicker
