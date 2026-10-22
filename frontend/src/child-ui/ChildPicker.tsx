import './ChildPicker.css'
import type { Child } from '../api/types'

type Props = {
  childList: Child[]
  onSelect: (child: Child) => void
}

// Used by the child side: pick who is reading, then enter that child's PIN
function ChildPicker({ childList, onSelect }: Props) {
  return (
    <main className="cp-picker">
      <span className="cp-shape cp-shape-mint" />
      <span className="cp-shape cp-shape-pink" />
      <span className="cp-shape cp-shape-peach" />
      <h1 className="cp-title">Who is reading?</h1>
      <div className="cp-list">
        {childList.map((c) => (
          <button key={c.id} className="cp-card" onClick={() => onSelect(c)}>
            <span className="cp-name">{c.name}</span>
            <span className="cp-likes">Likes: {c.interests.join(', ')}</span>
          </button>
        ))}
      </div>
    </main>
  )
}

export default ChildPicker
