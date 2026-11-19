import { useState } from 'react'
import AddChildForm from './AddChildForm'
import { deleteChild, getChildPin, setChildPin } from '../api/children'
import type { Child, Dashboard } from '../api/types'
import { lookFor } from '../child-ui/interestLooks'

type Props = {
  child: Child | undefined
  childList: Child[]
  onChange: (child: Child) => void
  onAdded: (child: Child) => void
  onRemoved: (child: Child) => void
  onChildrenChanged: () => void
  dashboard: Dashboard | null
  failed: boolean
  onRetry: () => void
}

function ParentHome({
  child,
  childList,
  onChange,
  onAdded,
  onRemoved,
  onChildrenChanged,
  dashboard,
  failed,
  onRetry,
}: Props) {
  const [adding, setAdding] = useState(false)
  const [removeFailed, setRemoveFailed] = useState(false)
  const [revealedPin, setRevealedPin] = useState<{ childId: string; pin: string } | null>(null)
  const [editingPin, setEditingPin] = useState(false)
  const [pinEntry, setPinEntry] = useState('')
  const [pinError, setPinError] = useState('')
  const [pinConfiguredChildren, setPinConfiguredChildren] = useState<string[]>([])
  const pinIsSet = Boolean(child && (child.pinSet || pinConfiguredChildren.includes(child.id)))
  // Same emoji and card color the child sees on the picker
  const [emoji, theme] = child ? lookFor(child.interests) : ['', 'default']

  async function handleRemove() {
    // Deleting can't be undone, so ask first
    if (!child || !window.confirm(`Remove ${child.name}? This deletes all of their reading progress and can't be undone.`)) return
    setRemoveFailed(false)
    try {
      await deleteChild(child.id)
      onRemoved(child)
    } catch {
      setRemoveFailed(true)
    }
  }

  async function handleShowPin() {
    if (!child) return
    if (revealedPin?.childId === child.id) {
      setRevealedPin(null)
      return
    }
    setPinError('')
    try {
      setRevealedPin({ childId: child.id, pin: await getChildPin(child.id) })
    } catch {
      setPinError("Couldn't retrieve this child's PIN. Try again.")
    }
  }

  async function handleSavePin(e: React.FormEvent) {
    e.preventDefault()
    if (!child) return
    if (!/^\d{4}$/.test(pinEntry)) {
      setPinError('PIN must be exactly 4 digits')
      return
    }
    setPinError('')
    try {
      await setChildPin(child.id, pinEntry)
      setPinConfiguredChildren((configured) => [...new Set([...configured, child.id])])
      setRevealedPin({ childId: child.id, pin: pinEntry })
      setPinEntry('')
      setEditingPin(false)
      onChildrenChanged()
    } catch {
      setPinError("Couldn't save this child's PIN. Try again.")
    }
  }

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
        <div className={`pd-card pd-theme-${theme}`}>
          <h2 className="pd-heading">{emoji} {child.name}'s week</h2>
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
      {child && !adding && (
        <div className={`pd-card pd-pin-card pd-theme-${theme}`}>
          <h2 className="pd-heading">{emoji} {child.name}'s PIN</h2>
          {pinIsSet && (
            <>
              <button type="button" className="pd-chip" onClick={handleShowPin}>
                {revealedPin?.childId === child.id ? 'Hide PIN' : 'Show PIN'}
              </button>
              {revealedPin?.childId === child.id && (
                <span className="pd-stat" aria-live="polite">
                  {revealedPin.pin}
                </span>
              )}
            </>
          )}
          {!editingPin ? (
            <button
              type="button"
              className="pd-chip"
              onClick={() => {
                setPinError('')
                setEditingPin(true)
              }}
            >
              {pinIsSet ? 'Change PIN' : 'Set PIN'}
            </button>
          ) : (
            <form className="pd-form" onSubmit={handleSavePin}>
              <label>
                New 4-digit PIN
                <input
                  className="pd-input"
                  type="password"
                  inputMode="numeric"
                  pattern="[0-9]{4}"
                  maxLength={4}
                  required
                  value={pinEntry}
                  onChange={(e) => setPinEntry(e.target.value.replace(/\D/g, '').slice(0, 4))}
                />
              </label>
              <div className="pd-form-buttons">
                <button type="submit">Save PIN</button>
                <button
                  type="button"
                  onClick={() => {
                    setEditingPin(false)
                    setPinEntry('')
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
          {pinError && <p className="pd-hint" role="alert">{pinError}</p>}
        </div>
      )}
      {child && !adding && (
        <div className={`pd-card pd-theme-${theme}`}>
          <h2 className="pd-heading">Remove {child.name}</h2>
          <p className="pd-stat">This deletes all of {child.name}'s reading progress.</p>
          <button type="button" className="pd-chip" onClick={handleRemove}>
            Remove {child.name}
          </button>
          {removeFailed && <p className="pd-hint">Couldn't remove {child.name}. Try again.</p>}
        </div>
      )}
    </section>
  )
}

export default ParentHome
