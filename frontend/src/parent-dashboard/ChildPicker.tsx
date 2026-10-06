// Static sample data until GET /children is connected
const children = [
  { id: 1, name: 'Mia', interests: ['dinosaurs', 'the ocean'] },
  { id: 2, name: 'Leo', interests: ['trucks', 'space'] },
]

type Props = {
  onSelect: (name: string) => void
}

function ChildPicker({ onSelect }: Props) {
  return (
    <main className="pd-picker">
      <h1 className="pd-title">Which child are you checking in on?</h1>
      <div className="pd-picker-list">
        {children.map((c) => (
          <button key={c.id} className="pd-card pd-picker-card" onClick={() => onSelect(c.name)}>
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
