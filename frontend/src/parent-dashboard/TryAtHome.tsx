type Props = {
  words: string[]
}

function TryAtHome({ words }: Props) {
  return (
    <section className="pd-card">
      <h2 className="pd-heading">Try at home</h2>
      <div className="pd-chips">
        {words.map((word) => (
          <span key={word} className="pd-chip">
            {word}
          </span>
        ))}
      </div>
    </section>
  )
}

export default TryAtHome
