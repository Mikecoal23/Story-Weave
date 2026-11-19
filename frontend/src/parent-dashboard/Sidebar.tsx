// Profile isn't in items: it sits at the bottom with Switch user and Log out
export type Tab = 'Home' | 'Progress' | 'Practice' | 'Profile'

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
      <button
        type="button"
        className={`pd-nav-item pd-profile ${active === 'Profile' ? 'active' : ''}`}
        onClick={() => onSelect('Profile')}
      >
        Profile
      </button>
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
