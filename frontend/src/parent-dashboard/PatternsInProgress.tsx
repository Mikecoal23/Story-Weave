// Static sample data: fill is the bar's width in percent
const patterns = [
  { label: 'sh', fill: 90 },
  { label: 'ch', fill: 65 },
  { label: 'blends', fill: 30 },
]

function PatternsInProgress() {
  return (
    <section className="pd-card">
      <h2 className="pd-heading">Patterns in progress</h2>
      {patterns.map((p) => (
        <div key={p.label} className="pd-bar-row">
          <span className="pd-bar-label">{p.label}</span>
          <div className="pd-bar-track">
            <div className="pd-bar-fill" style={{ width: `${p.fill}%` }} />
          </div>
        </div>
      ))}
    </section>
  )
}

export default PatternsInProgress
