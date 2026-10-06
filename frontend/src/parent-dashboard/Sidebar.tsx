export type Tab = 'Home' | 'Progress' | 'Practice'

const items: Tab[] = ['Home', 'Progress', 'Practice']

type Props = {
  active: Tab
  onSelect: (tab: Tab) => void
}

// Replaces the phone's bottom nav
function Sidebar({ active, onSelect }: Props) {
  return (
    <nav className="pd-sidebar">
      <h2 className="pd-brand">StoryWeave</h2>
      {items.map((item) => (
        <button
          key={item}
          type="button"
          className={`pd-nav-item ${item === active ? 'active' : ''}`}
          onClick={() => onSelect(item)}
        >
          {item}
        </button>
      ))}
    </nav>
  )
}

export default Sidebar
