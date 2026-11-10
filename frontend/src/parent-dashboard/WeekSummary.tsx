import type { Dashboard } from '../api/types'

type Props = {
  childName: string
  dashboard: Dashboard
}

function WeekSummary({ childName, dashboard }: Props) {
  // "sh", "sh and ch", "sh, ch, and th"; empty means nothing to say yet
  const workingOn = new Intl.ListFormat('en').format(dashboard.working_on)
  const parts = [
    workingOn && `Working on: ${workingOn}.`,
    dashboard.strongest && `${dashboard.strongest} is going really well.`,
  ].filter(Boolean)

  return (
    <section>
      <h1 className="pd-title">{childName}'s week</h1>
      <div className="pd-note">
        {dashboard.sessions === 0
          ? `${childName} hasn't read yet. Progress shows up after the first story.`
          : parts.join(' ') || `Keep reading with ${childName} to see what they're working on.`}
      </div>
    </section>
  )
}

export default WeekSummary
