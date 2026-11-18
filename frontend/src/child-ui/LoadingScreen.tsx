import { useEffect, useRef, useState } from 'react'
import './EndScreens.css'
import { generateStory } from '../api/stories'
import type { Story } from '../api/types'

// How long to wait before offering "Try again" while a story is still generating
const SLOW_MS = 20000

type Props = {
  childId: string
  onDone: (story: Story) => void
}

function LoadingScreen({ childId, onDone }: Props) {
  const [failed, setFailed] = useState(false)
  // Bumping this re-runs the effect, which is how "Try again" re-requests the story
  const [attempt, setAttempt] = useState(0)
  // True once the story has taken longer than SLOW_MS, so the child isn't stuck on a spinner
  const [slow, setSlow] = useState(false)
  // The request for the current child and attempt. React's StrictMode runs this effect
  // twice in development; reusing the request means one story is generated, not two.
  const request = useRef<{ key: string; story: Promise<Story> } | null>(null)

  useEffect(() => {
    // Ignore the result if the screen was left before the story arrived
    let cancelled = false
    const key = `${childId}:${attempt}`
    if (request.current?.key !== key) {
      request.current = { key, story: generateStory(childId) }
    }
    request.current.story
      .then((story) => {
        if (!cancelled) onDone(story)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })
    return () => {
      cancelled = true
    }
  }, [childId, onDone, attempt])

  // Restart the timer on every attempt; clearing it stops it firing after the story arrives
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), SLOW_MS)
    return () => clearTimeout(timer)
  }, [attempt])

  function retry() {
    setFailed(false)
    setSlow(false)
    setAttempt(attempt + 1)
  }

  if (failed)
    return (
      <main className="start">
        <h1 className="start-title">Couldn't weave a story</h1>
        <button className="start-btn" onClick={retry}>
          Try again
        </button>
      </main>
    )

  return (
    <main className="start">
      <div className="spinner" />
      <h1 className="start-title">Weaving your story…</h1>
      {slow && (
        <>
          <p className="start-sub">This is taking longer than usual.</p>
          <button className="start-btn secondary" onClick={retry}>
            Try again
          </button>
        </>
      )}
    </main>
  )
}

export default LoadingScreen
