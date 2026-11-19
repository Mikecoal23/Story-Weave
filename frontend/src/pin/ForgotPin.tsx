import { useState } from 'react'
import './PinScreen.css'
import { emailMatches } from '../api/caregivers'

type Props = {
  onVerified: () => void // email matched: go set a new PIN
  onBack: () => void
}

// Asking for the account email keeps a child from resetting the parent PIN
function ForgotPin({ onVerified, onBack }: Props) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (emailMatches(email)) onVerified()
    else setError("That email doesn't match this account.")
  }

  return (
    <main className="pin">
      <span className="pin-shape pin-shape-mint" />
      <span className="pin-shape pin-shape-pink" />
      <span className="pin-shape pin-shape-peach" />
      <button type="button" className="pin-back" onClick={onBack}>
        ← Back
      </button>
      <form className="pin-card" onSubmit={handleSubmit}>
        <h1 className="pin-title">Forgot your PIN?</h1>
        <label className="pin-label">
          Enter your account email
          <input
            className="pin-input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <p className="pin-error" role="alert">{error}</p>
        <button type="submit" className="pin-submit">
          Continue
        </button>
      </form>
    </main>
  )
}

export default ForgotPin
