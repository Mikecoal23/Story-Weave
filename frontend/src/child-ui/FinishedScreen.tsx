import './EndScreens.css'

type Props = {
  lineCount: number
  onNewStory: () => void
  onDone: () => void // back to "Who is reading?"
}

function FinishedScreen({ lineCount, onNewStory, onDone }: Props) {
  return (
    <main className="start">
      <h1 className="start-title">Great reading!</h1>
      <p className="start-sub">You read {lineCount} lines.</p>
      <button className="start-btn" onClick={onNewStory}>
        New story
      </button>
      <button className="start-btn secondary" onClick={onDone}>
        Done
      </button>
    </main>
  )
}

export default FinishedScreen
