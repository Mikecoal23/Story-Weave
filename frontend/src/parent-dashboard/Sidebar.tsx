export type Tab = 'Home' | 'Progress' | 'Practice'

const items: Tab[] = ['Home', 'Progress', 'Practice']

type Props = {
  active: Tab
  onSelect: (tab: Tab) => void
  onSwitchUser: () => void
  onLogout: () => void
}

// Replaces the phone's bottom nav
function Sidebar({ active, onSelect, onSwitchUser, onLogout }: Props) {
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
      {/* Back to "Who's using StoryWeave?" without logging out */}
      <button type="button" className="pd-nav-item pd-switch" onClick={onSwitchUser}>
        Switch user
      </button>
      <button type="button" className="pd-nav-item pd-logout" onClick={onLogout}>
        Log out
      </button>
    </nav>
  )
}

export default Sidebar
