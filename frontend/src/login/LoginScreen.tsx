import { useState } from 'react'
import './LoginScreen.css'

type Props = {
  onSuccess: () => void
  loadError: string // set when login worked but the children couldn't be loaded
}

// Temporary bypass until POST /caregivers/{id}/session is connected
const USERNAME = 'admin'
const PASSWORD = '123'

function LoginScreen({ onSuccess, loadError }: Props) {
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
      <section className="login-hero">
        <span className="login-shape login-shape-mint" />
        <span className="login-shape login-shape-pink" />
        <span className="login-shape login-shape-cream" />
        <h1 className="login-title">StoryWeave</h1>
        <p className="login-tagline">Read a story made just for you</p>
      </section>
      <form className="login-form" onSubmit={handleSubmit}>
        <h2 className="login-heading">Log in</h2>
        <label className="login-label">
          Username
          <input
            className="login-input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label className="login-label">
          Password
          <input
            className="login-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <p className="login-error">{error ? 'Wrong username or password' : loadError}</p>
        <button type="submit" className="login-btn">
          Log in
        </button>
      </form>
      <span className="login-shape login-shape-lime" />
      <span className="login-shape login-shape-peach" />
    </main>
  )
}

export default LoginScreen
