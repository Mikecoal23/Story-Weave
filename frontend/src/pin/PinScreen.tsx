import { useState } from 'react'
import './PinScreen.css'

type Props = {
  title: string
  expectedPin: string
  onSuccess: () => void
  kid?: boolean // bigger, friendlier style for the child PIN
}

const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', '⌫']

function PinScreen({ title, expectedPin, onSuccess, kid }: Props) {
  // Kept as a string so leading zeros survive ("0420")
  const [digits, setDigits] = useState('')
  const [wrong, setWrong] = useState(false)

  function press(key: string) {
    if (key === '⌫') {
      setDigits(digits.slice(0, -1))
      return
    }
    const next = digits + key
    if (next.length < 4) {
      setDigits(next)
      setWrong(false)
    } else if (next === expectedPin) {
      onSuccess()
    } else {
      setDigits('')
      setWrong(true)
    }
  }

  return (
    <main className={`pin ${kid ? 'pin-kid' : ''}`}>
      <h1 className="pin-title">{title}</h1>
      <div className="pin-dots">
        {[0, 1, 2, 3].map((i) => (
          <span key={i} className={`pin-dot ${i < digits.length ? 'filled' : ''}`} />
        ))}
      </div>
      <p className="pin-error">{wrong ? 'Try again' : ''}</p>
      <div className="pin-keys">
        {keys.map((key, i) =>
          key === '' ? (
            <span key={i} />
          ) : (
            <button key={i} type="button" className="pin-key" onClick={() => press(key)}>
              {key}
            </button>
          ),
        )}
      </div>
    </main>
  )
}

export default PinScreen
