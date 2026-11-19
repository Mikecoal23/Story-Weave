import { useState } from 'react'
import { setCaregiverPin } from '../api/caregivers'

function ParentProfile() {
  const [editing, setEditing] = useState(false)
  const [pin, setPin] = useState('')
  const [confirm, setConfirm] = useState('')
  const [message, setMessage] = useState('')

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    if (!/^\d{4}$/.test(pin)) {
      setMessage('PIN must be exactly 4 digits')
      return
    }
    if (pin !== confirm) {
      setMessage("The PINs don't match")
      return
    }
    try {
      await setCaregiverPin(pin)
      setEditing(false)
      setPin('')
      setConfirm('')
      setMessage('PIN updated')
    } catch {
      setMessage("Couldn't update your PIN. Try again.")
    }
  }

  // Keeps only digits, at most 4 (same as the child PIN input)
  const digitsOnly = (value: string) => value.replace(/\D/g, '').slice(0, 4)

  return (
    <section>
      <h1 className="pd-title">Profile</h1>
      <div className="pd-card">
        <h2 className="pd-heading">Parent PIN</h2>
        {!editing ? (
          <button
            type="button"
            className="pd-chip"
            onClick={() => {
              setMessage('')
              setEditing(true)
            }}
          >
            Reset PIN
          </button>
        ) : (
          <form className="pd-form" onSubmit={handleSave}>
            <label>
              New 4-digit PIN
              <input
                className="pd-input"
                type="password"
                inputMode="numeric"
                maxLength={4}
                required
                value={pin}
                onChange={(e) => setPin(digitsOnly(e.target.value))}
              />
            </label>
            <label>
              Confirm PIN
              <input
                className="pd-input"
                type="password"
                inputMode="numeric"
                maxLength={4}
                required
                value={confirm}
                onChange={(e) => setConfirm(digitsOnly(e.target.value))}
              />
            </label>
            <div className="pd-form-buttons">
              <button type="submit">Save PIN</button>
              <button
                type="button"
                onClick={() => {
                  setEditing(false)
                  setPin('')
                  setConfirm('')
                  setMessage('')
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        )}
        {message && <p className="pd-hint" role="alert">{message}</p>}
      </div>
    </section>
  )
}

export default ParentProfile
