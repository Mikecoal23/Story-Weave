import { useState } from 'react'
import './ChildApp.css'
import StartScreen from './StartScreen'
import LoadingScreen from './LoadingScreen'
import FinishedScreen from './FinishedScreen'
import TopBar from './TopBar'
import SentenceReader from './SentenceReader'
import Controls from './Controls'
import { startSession } from '../api/sessions'
import type { Child, Story, WordScore } from '../api/types'

type Screen = 'pick' | 'loading' | 'reader' | 'finished'

type Props = {
  child: Child
  onSwitchReader: () => void
}

function ChildApp({ child, onSwitchReader }: Props) {
  const [screen, setScreen] = useState<Screen>('pick')
  // The story the backend generated, and which of its lines is on screen
  const [story, setStory] = useState<Story | null>(null)
  const [lineIndex, setLineIndex] = useState(0)
  // How each word of the current line was read; null until the line has been scored
  const [scores, setScores] = useState<WordScore[] | null>(null)

  // The reading session the audio uploads belong to
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessionError, setSessionError] = useState(false)

  async function handleStory(newStory: Story) {
    setStory(newStory)
    setLineIndex(0)
    setScores(null)
    setSessionId(null)
    setSessionError(false)
    setScreen('reader')
    try {
      setSessionId((await startSession(child.id, newStory.id)).id)
    } catch {
      // Mic stays disabled until a session exists, so tell the reader why
      setSessionError(true)
    }
  }

  function handleNext() {
    setScores(null)
    if (story && lineIndex + 1 < story.lines.length) setLineIndex(lineIndex + 1)
    else setScreen('finished')
  }

  if (screen === 'pick') return <StartScreen onStart={() => setScreen('loading')} />
  if (screen === 'loading') return <LoadingScreen childId={child.id} onDone={handleStory} />
  if (screen === 'finished')
    return (
      <FinishedScreen
        lineCount={story?.lines.length ?? 0}
        onNewStory={() => setScreen('loading')}
        onDone={onSwitchReader}
      />
    )

  return (
    <main className="screen">
      <TopBar
        onHome={onSwitchReader}
        current={lineIndex + 1}
        total={story?.lines.length ?? 1}
      />
      <SentenceReader line={story?.lines[lineIndex] ?? ''} scores={scores} />
      {sessionError && <p>We couldn't start your reading session. Try again.</p>}
      <Controls
        sessionId={sessionId}
        lineNumber={lineIndex + 1}
        onScored={setScores}
        onNext={handleNext}
      />
    </main>
  )
}

export default ChildApp
