import { useState } from 'react'
import './StartScreen.css'

type Props = {
  onStart: () => void
}

// Placeholder titles until stories come from the backend
const STORIES = ['The Brave Little Fox', 'Space Trip to the Moon', 'The Sleepy Dragon']

function StartScreen({ onStart }: Props) {
  const [picked, setPicked] = useState(STORIES[0])

  return (
    <main className="start">
      <h1 className="start-title">Pick a story</h1>
      <div className="start-stories">
        {STORIES.map((title) => (
          <button
            key={title}
            className={`start-story${title === picked ? ' selected' : ''}`}
            onClick={() => setPicked(title)}
          >
            {title}
          </button>
        ))}
      </div>
      <button className="start-btn" onClick={onStart}>
        Start
      </button>
    </main>
  )
}

export default StartScreen
