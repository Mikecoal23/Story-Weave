import './ParentDashboard.css'
import { children, type Child } from './mockChildren'

type Props = {
  onSelect: (child: Child) => void
}

// Used by the child side: pick who is reading, then enter that child's PIN
function ChildPicker({ onSelect }: Props) {
  return (
    <main className="pd-picker">
      <h1 className="pd-title">Who is reading?</h1>
      <div className="pd-picker-list">
        {children.map((c) => (
          <button key={c.id} className="pd-card pd-picker-card" onClick={() => onSelect(c)}>
            <span className="pd-heading">{c.name}</span>
            <span className="pd-stat">Likes: {c.interests.join(', ')}</span>
          </button>
        ))}
      </div>
      <p className="pd-hint">Adding a child will be available once the backend is connected.</p>
    </main>
  )
}

export default ChildPicker
