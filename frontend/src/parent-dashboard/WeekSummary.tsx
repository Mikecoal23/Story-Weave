import type { Dashboard } from '../api/types'

type Props = {
  dashboard: Dashboard
}

function WeekSummary({ dashboard }: Props) {
  return (
    <section>
      <h1 className="pd-title">Your child's week</h1>
      <div className="pd-note">
        Working on: {dashboard.workingOn.join(' and ')}. Great progress on {dashboard.strongest}!
      </div>
    </section>
  )
}

export default WeekSummary
