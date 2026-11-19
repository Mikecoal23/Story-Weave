import { useState } from 'react'
import './PinScreen.css'

type Props = {
  title: string
  onSubmit: (pin: string) => Promise<boolean>
  onSuccess: () => void
  onBack: () => void
  onForgot?: () => void // only the parent PIN passes this, which shows "Forgot PIN?"
  kid?: boolean // bigger, friendlier style for the child PIN
}

const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', '⌫']

function PinScreen({ title, onSubmit, onSuccess, onBack, onForgot, kid }: Props) {
  // Kept as a string so leading zeros survive ("0420")
  const [digits, setDigits] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function press(key: string) {
    if (key === '⌫') {
      setDigits(digits.slice(0, -1))
      return
    }
    if (busy) return
    const next = digits + key
    if (next.length < 4) {
      setDigits(next)
      setError('')
    } else {
      setBusy(true)
      setError('')
      try {
        if (await onSubmit(next)) {
          onSuccess()
        } else {
          setDigits('')
          setError('Try again')
        }
      } catch (err) {
        setDigits('')
        setError(
          String(err).includes('429')
            ? 'Too many tries. Please wait 15 minutes.'
            : "Couldn't check the PIN. Try again.",
        )
      } finally {
        setBusy(false)
      }
    }
  }

  return (
    <main className={`pin ${kid ? 'pin-kid' : ''}`}>
      <span className="pin-shape pin-shape-mint" />
      <span className="pin-shape pin-shape-pink" />
      <span className="pin-shape pin-shape-peach" />
      <button type="button" className="pin-back" onClick={onBack}>
        ← Back
      </button>
      <div className="pin-card">
        <h1 className="pin-title">{title}</h1>
        <div className="pin-dots">
          {[0, 1, 2, 3].map((i) => (
            <span key={i} className={`pin-dot ${i < digits.length ? 'filled' : ''}`} />
          ))}
        </div>
        <p className="pin-error" role="alert">{error}</p>
        <div className="pin-keys">
          {keys.map((key, i) =>
            key === '' ? (
              <span key={i} />
            ) : (
              <button
                key={i}
                type="button"
                className="pin-key"
                disabled={busy}
                onClick={() => press(key)}
              >
                {key}
              </button>
            ),
          )}
        </div>
        {onForgot && (
          <button type="button" className="pin-forgot" onClick={onForgot}>
            Forgot PIN?
          </button>
        )}
      </div>
    </main>
  )
}

export default PinScreen
