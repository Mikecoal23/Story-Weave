import { useEffect, useState } from 'react'
import './LoginScreen.css'
import { request } from '../api/client'
import { createAccount, login } from '../api/caregivers'

type Props = {
  onSuccess: () => void
  loadError: string // set when login worked but the children couldn't be loaded
}

function LoginScreen({ onSuccess, loadError }: Props) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  // Wiring check: can the frontend reach the backend's GET /health?
  const [backend, setBackend] = useState<'checking' | 'ok' | 'down'>('checking')

  useEffect(() => {
    request<{ status: string }>('/health')
      .then((data) => setBackend(data.status === 'ok' ? 'ok' : 'down'))
      .catch(() => setBackend('down'))
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      if (mode === 'login') await login(email)
      else await createAccount(name, email)
    } catch (err) {
      // request() errors start with the status code, e.g. "404 Not Found"
      const text = String(err)
      if (text.includes('404')) setError('No account for that email')
      else if (text.includes('409')) setError('That email already has an account')
      else setError("Couldn't reach the server")
      return
    }
    setError('')
    onSuccess()
  }

  function switchMode() {
    setMode(mode === 'login' ? 'signup' : 'login')
    setError('')
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
        <h2 className="login-heading">{mode === 'login' ? 'Log in' : 'Create account'}</h2>
        {mode === 'signup' && (
          <label className="login-label">
            Your name
            <input
              className="login-input"
              required
              maxLength={120}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
        )}
        <label className="login-label">
          Email
          <input
            className="login-input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <p className="login-error">{error || loadError}</p>
        <button type="submit" className="login-btn">
          {mode === 'login' ? 'Log in' : 'Create account'}
        </button>
        <button type="button" className="login-switch" onClick={switchMode}>
          {mode === 'login' ? 'New here? Create an account' : 'Already have an account? Log in'}
        </button>
        <p className="login-status">
          Backend: {backend === 'ok' ? 'connected' : backend === 'down' ? 'not reachable' : 'checking…'}
        </p>
      </form>
      <span className="login-shape login-shape-lime" />
      <span className="login-shape login-shape-peach" />
    </main>
  )
}

export default LoginScreen
