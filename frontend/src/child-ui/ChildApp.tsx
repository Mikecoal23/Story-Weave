import { useState } from 'react'
import './ChildApp.css'
import StartScreen from './StartScreen'
import LoadingScreen from './LoadingScreen'
import FinishedScreen from './FinishedScreen'
import TopBar from './TopBar'
import SentenceReader from './SentenceReader'
import Controls from './Controls'
import type { Child, Story } from '../api/types'

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

  function handleStory(newStory: Story) {
    setStory(newStory)
    setLineIndex(0)
    setScreen('reader')
  }

  function handleNext() {
    if (story && lineIndex + 1 < story.lines.length) setLineIndex(lineIndex + 1)
    else setScreen('finished')
  }

  if (screen === 'pick') return <StartScreen onStart={() => setScreen('loading')} />
  if (screen === 'loading') return <LoadingScreen childId={child.id} onDone={handleStory} />
  if (screen === 'finished') return <FinishedScreen onNewStory={() => setScreen('loading')} />

  return (
    <main className="screen">
      <TopBar
        onHome={onSwitchReader}
        current={lineIndex + 1}
        total={story?.lines.length ?? 1}
      />
      <SentenceReader line={story?.lines[lineIndex] ?? ''} />
      <Controls onNext={handleNext} />
    </main>
  )
}

export default ChildApp
