function TopBar() {
  return (
    <header className="top-bar">
      <button className="btn home" onClick={() => console.log('Home')}>
        Home
      </button>
      <h1 className="title">StoryWeave</h1>
    </header>
  )
}

export default TopBar
