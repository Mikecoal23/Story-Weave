import { useEffect } from 'react'
import './EndScreens.css'

type Props = {
  onDone: () => void
}

function LoadingScreen({ onDone }: Props) {
  // Mock wait; the real version will finish when the backend returns the story
  useEffect(() => {
    const timer = setTimeout(onDone, 2000)
    return () => clearTimeout(timer)
  }, [onDone])

  return (
    <main className="start">
      <div className="spinner" />
      <h1 className="start-title">Weaving your story…</h1>
    </main>
  )
}

export default LoadingScreen
