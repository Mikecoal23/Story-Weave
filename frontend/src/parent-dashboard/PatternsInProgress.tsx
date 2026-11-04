import type { Dashboard } from '../api/types'

type Props = {
  patterns: Dashboard['patterns']
}

function PatternsInProgress({ patterns }: Props) {
  return (
    <section className="pd-card">
      <h2 className="pd-heading">Patterns in progress</h2>
      {patterns.length === 0 && <p className="pd-hint">Patterns show up after the first story.</p>}
      {patterns.map((p) => (
        <div key={p.label} className="pd-bar-row">
          <span className="pd-bar-label">{p.label}</span>
          {/* role + aria-valuenow let screen readers announce the percent the bar shows */}
          <div
            className="pd-bar-track"
            role="progressbar"
            aria-label={`${p.label} mastery`}
            aria-valuenow={p.fill}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div className="pd-bar-fill" style={{ width: `${p.fill}%` }} />
          </div>
          <span className="pd-bar-value">{p.fill}%</span>
        </div>
      ))}
    </section>
  )
}

export default PatternsInProgress
