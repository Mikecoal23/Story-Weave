type Props = {
  onNext: () => void
}

function Controls({ onNext }: Props) {
  return (
    <>
      <button className="mic" onClick={() => console.log('MIC')}>
         Click to speak
      </button>
      <footer className="bottom-bar">
        <button className="btn btn-outline" onClick={() => console.log('Hear it')}>
          Hear it
        </button>
        <button className="btn btn-green" onClick={onNext}>
          Next line
        </button>
      </footer>
    </>
  )
}

export default Controls
