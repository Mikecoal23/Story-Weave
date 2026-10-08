type Props = {
  onHome: () => void
}

function TopBar({ onHome }: Props) {
  return (
    <header className="top-bar">
      <button className="btn home" onClick={onHome}>
        Switch reader
      </button>
      <h1 className="title">StoryWeave</h1>
    </header>
  )
}

export default TopBar
