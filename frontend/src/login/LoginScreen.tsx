import { useState } from 'react'
import './LoginScreen.css'

type Props = {
  onSuccess: () => void
}

// Temporary bypass until POST /caregivers/{id}/session is connected
const USERNAME = 'admin'
const PASSWORD = '123'

function LoginScreen({ onSuccess }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (username === USERNAME && password === PASSWORD) onSuccess()
    else setError(true)
  }

  return (
    <main className="login">
      <h1 className="login-title">StoryWeave</h1>
      <form className="login-form" onSubmit={handleSubmit}>
        <input
          className="login-input"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          className="login-input"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <p className="login-error">{error ? 'Wrong username or password' : ''}</p>
        <button type="submit" className="login-btn">
          Log in
        </button>
      </form>
    </main>
  )
}

export default LoginScreen
