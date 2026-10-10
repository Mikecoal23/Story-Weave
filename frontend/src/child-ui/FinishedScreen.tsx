import './EndScreens.css'

type Props = {
  onNewStory: () => void
}

function FinishedScreen({ onNewStory }: Props) {
  return (
    <main className="start">
      <h1 className="start-title">Great reading! 🎉</h1>
      <button className="start-btn" onClick={onNewStory}>
        New story
      </button>
    </main>
  )
}

export default FinishedScreen
