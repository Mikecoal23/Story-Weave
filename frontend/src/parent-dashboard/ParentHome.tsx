import { children, type Child } from './mockChildren'

// Static sample stats (same for every child) until the dashboard endpoint is connected
const week = {
  sessions: 3,
  minutes: 12,
  lastStory: 'The Shell on the Beach',
}

type Props = {
  child: Child
  onChange: (child: Child) => void
}

function ParentHome({ child, onChange }: Props) {
  return (
    <section>
      <h1 className="pd-title">Welcome back</h1>
      <select
        className="pd-select"
        value={child.id}
        onChange={(e) => onChange(children.find((c) => c.id === Number(e.target.value))!)}
      >
        {children.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
      <div className="pd-card">
        <h2 className="pd-heading">{child.name}'s week</h2>
        <p className="pd-stat">
          {week.sessions} reading sessions · {week.minutes} minutes
        </p>
        <p className="pd-stat">Last story: {week.lastStory}</p>
        <p className="pd-stat">Working on: sh and ch</p>
        <p className="pd-hint">See the Progress tab for more detail.</p>
      </div>
    </section>
  )
}

export default ParentHome
