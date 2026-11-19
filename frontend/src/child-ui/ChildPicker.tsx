import './ChildPicker.css'
import type { Child } from '../api/types'
import { lookFor } from './interestLooks'

type Props = {
  childList: Child[]
  onSelect: (child: Child) => void
  onBack: () => void // back to "Who's using StoryWeave?"
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
          <button
            key={c.id}
            className={`cp-card cp-theme-${theme}`}
            disabled={!c.pinSet}
            onClick={() => onSelect(c)}
          >
            <span className="cp-emoji" aria-hidden="true">{emoji}</span>
            <span className="cp-name">{c.name}</span>
            <span className="cp-likes">
              {c.pinSet ? `Likes: ${c.interests.join(', ')}` : 'Ask a grown-up to set a PIN'}
            </span>
          </button>
          )
        })}
      </div>
    </main>
  )
}

export default ChildPicker
