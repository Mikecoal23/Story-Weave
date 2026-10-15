import './ParentDashboard.css'
import type { Child } from '../api/types'

type Props = {
  childList: Child[]
  onSelect: (child: Child) => void
}

// Used by the child side: pick who is reading, then enter that child's PIN
function ChildPicker({ childList, onSelect }: Props) {
  return (
    <main className="pd-picker">
      <h1 className="pd-title">Who is reading?</h1>
      <div className="pd-picker-list">
        {childList.map((c) => (
          <button key={c.id} className="pd-card pd-picker-card" onClick={() => onSelect(c)}>
            <span className="pd-heading">{c.name}</span>
            <span className="pd-stat">Likes: {c.interests.join(', ')}</span>
          </button>
        ))}
      </div>
    </main>
  )
}

export default ChildPicker
