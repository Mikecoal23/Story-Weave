import { useState } from 'react'
import AddChildForm from './AddChildForm'
import type { Child, Dashboard } from '../api/types'

type Props = {
  child: Child
  childList: Child[]
  onChange: (child: Child) => void
  onAdded: (child: Child) => void
  dashboard: Dashboard | null
  failed: boolean
}

function ParentHome({ child, childList, onChange, onAdded, dashboard, failed }: Props) {
  const [adding, setAdding] = useState(false)

  return (
    <section>
      <h1 className="pd-title">Welcome back</h1>
      <select
        className="pd-select"
        value={child.id}
        onChange={(e) => onChange(childList.find((c) => c.id === e.target.value)!)}
      >
        {childList.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
      <button type="button" className="pd-add" onClick={() => setAdding(true)}>
        Add child
      </button>
      {adding ? (
        <AddChildForm
          onAdded={(newChild) => {
            setAdding(false)
            onAdded(newChild)
          }}
          onCancel={() => setAdding(false)}
        />
      ) : dashboard ? (
        <div className="pd-card">
          <h2 className="pd-heading">{child.name}'s week</h2>
          <p className="pd-stat">
            {dashboard.sessions} reading sessions · {dashboard.minutes} minutes
          </p>
          <p className="pd-stat">Last story: {dashboard.lastStory}</p>
          <p className="pd-stat">Working on: {dashboard.workingOn.join(' and ')}</p>
          <p className="pd-hint">See the Progress tab for more detail.</p>
        </div>
      ) : (
        <p className="pd-hint">{failed ? "Couldn't load the dashboard" : 'Loading…'}</p>
      )}
    </section>
  )
}

export default ParentHome
