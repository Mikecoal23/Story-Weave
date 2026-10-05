import './EntryScreen.css'

type Props = {
  onSelect: (role: 'child' | 'parent') => void
}

function EntryScreen({ onSelect }: Props) {
  return (
    <main className="entry">
      <h1 className="entry-title">Who's using StoryWeave?</h1>
      <div className="entry-buttons">
        <button className="entry-btn" onClick={() => onSelect('child')}>
          Child
        </button>
        <button className="entry-btn" onClick={() => onSelect('parent')}>
          Parent
        </button>
      </div>
    </main>
  )
}

export default EntryScreen
