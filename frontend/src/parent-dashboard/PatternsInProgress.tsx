import type { Dashboard } from '../api/types'

type Props = {
  patterns: Dashboard['patterns']
}

function PatternsInProgress({ patterns }: Props) {
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
