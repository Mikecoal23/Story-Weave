import { useState } from 'react'
import './ChildApp.css'
import StartScreen from './StartScreen'
import LoadingScreen from './LoadingScreen'
import FinishedScreen from './FinishedScreen'
import TopBar from './TopBar'
import SentenceReader from './SentenceReader'
import Controls from './Controls'

type Screen = 'pick' | 'loading' | 'reader' | 'finished'

type Props = {
  onSwitchReader: () => void
}

function ChildApp({ onSwitchReader }: Props) {
  const [screen, setScreen] = useState<Screen>('pick')

  if (screen === 'pick') return <StartScreen onStart={() => setScreen('loading')} />
  if (screen === 'loading') return <LoadingScreen onDone={() => setScreen('reader')} />
  if (screen === 'finished') return <FinishedScreen onNewStory={() => setScreen('loading')} />

  return (
    <main className="screen">
      <TopBar onHome={onSwitchReader} />
      <SentenceReader />
      <Controls onNext={() => setScreen('finished')} />
    </main>
  )
}

export default ChildApp
