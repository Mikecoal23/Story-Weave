import { useState } from 'react'
import './ChildApp.css'
import StartScreen from './StartScreen'
import TopBar from './TopBar'
import SentenceReader from './SentenceReader'
import Controls from './Controls'

function ChildApp() {
  // false = story pick screen; true = the reader
  const [started, setStarted] = useState(false)

  if (!started) return <StartScreen onStart={() => setStarted(true)} />

  return (
    <main className="screen">
      <TopBar />
      <SentenceReader />
      <Controls />
    </main>
  )
}

export default ChildApp
