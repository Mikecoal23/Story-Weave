// Static sample data until the dashboard endpoint is connected
const child = {
  name: 'Mia',
  sessions: 3,
  minutes: 12,
  lastStory: 'The Shell on the Beach',
}

function ParentHome() {
  return (
    <section>
      <h1 className="pd-title">Welcome back</h1>
      <div className="pd-card">
        <h2 className="pd-heading">{child.name}'s week</h2>
        <p className="pd-stat">
          {child.sessions} reading sessions · {child.minutes} minutes
        </p>
        <p className="pd-stat">Last story: {child.lastStory}</p>
        <p className="pd-stat">Working on: sh and ch</p>
        <p className="pd-hint">See the Progress tab for more detail.</p>
      </div>
    </section>
  )
}

export default ParentHome
