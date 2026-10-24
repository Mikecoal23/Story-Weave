import { useEffect, useRef, useState } from 'react'
import './EndScreens.css'
import { generateStory } from '../api/stories'
import type { Story } from '../api/types'

type Props = {
  childId: string
  onDone: (story: Story) => void
}

function LoadingScreen({ childId, onDone }: Props) {
  const [failed, setFailed] = useState(false)
  // Bumping this re-runs the effect, which is how "Try again" re-requests the story
  const [attempt, setAttempt] = useState(0)
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

  function retry() {
    setFailed(false)
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
    </main>
  )
}

export default LoadingScreen
