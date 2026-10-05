const words = ['shop', 'shell', 'shed']

function TryAtHome() {
  return (
    <section className="pd-card">
      <h2 className="pd-heading">Try at home</h2>
      <div className="pd-chips">
        {words.map((word) => (
          <button key={word} type="button" className="pd-chip">
            {word}
          </button>
        ))}
      </div>
    </section>
  )
}

export default TryAtHome
