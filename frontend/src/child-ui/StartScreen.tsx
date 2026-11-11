import './StartScreen.css'

type Props = {
  onStart: () => void
}

function StartScreen({ onStart }: Props) {
  return (
    <main className="start">
      <h1 className="start-title">Ready to read?</h1>
      <button className="start-btn" onClick={onStart}>
        Start
      </button>
    </main>
  )
}

export default StartScreen
