import { useState } from 'react'
import AddChildForm from './AddChildForm'
import type { Child, Dashboard } from '../api/types'

type Props = {
  child: Child | undefined
  childList: Child[]
  onChange: (child: Child) => void
  onAdded: (child: Child) => void
  dashboard: Dashboard | null
  failed: boolean
  onRetry: () => void
}

function ParentHome({ child, childList, onChange, onAdded, dashboard, failed, onRetry }: Props) {
  const [adding, setAdding] = useState(false)

  return (
    <section>
      <h1 className="pd-title">Welcome back</h1>
      {child && (
        <>
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
        </>
      )}
      {!child ? (
        <>
          <p className="pd-hint">No readers yet. Add your first child to get started.</p>
          <AddChildForm onAdded={onAdded} onCancel={() => {}} />
        </>
      ) : adding ? (
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
          {dashboard.sessions === 0 ? (
            <p className="pd-stat">
              {child.name} hasn't read yet. Their first story will show up here.
            </p>
          ) : (
            <>
              <p className="pd-stat">
                {dashboard.sessions} reading sessions
              </p>
              <p className="pd-stat">Last story: {dashboard.last_story}</p>
              <p className="pd-hint">See the Progress tab for more detail.</p>
            </>
          )}
        </div>
      ) : failed ? (
        <>
          <p className="pd-hint">Couldn't load the dashboard</p>
          <button type="button" className="pd-chip" onClick={onRetry}>
            Try again
          </button>
        </>
      ) : (
        <p className="pd-hint">Loading…</p>
      )}
    </section>
  )
}

export default ParentHome
