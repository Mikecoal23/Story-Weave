// Replaces the phone's bottom nav. Buttons do nothing.
const items = ['Home', 'Progress', 'Practice']

function Sidebar() {
  return (
    <nav className="pd-sidebar">
      <h2 className="pd-brand">StoryWeave</h2>
      {items.map((item) => (
        <button
          key={item}
          type="button"
          className={`pd-nav-item ${item === 'Progress' ? 'active' : ''}`}
        >
          {item}
        </button>
      ))}
    </nav>
  )
}

export default Sidebar
