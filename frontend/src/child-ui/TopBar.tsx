type Props = {
  onHome: () => void
  current: number
  total: number
}

function TopBar({ onHome, current, total }: Props) {
  return (
    <header className="top-bar">
      <button className="close" onClick={onHome} aria-label="Switch reader">
        ✕
      </button>
      <div className="progress">
        <div className="progress-fill" style={{ width: `${(current / total) * 100}%` }} />
      </div>
      <span className="count">
        {current}/{total}
      </span>
    </header>
  )
}

export default TopBar
