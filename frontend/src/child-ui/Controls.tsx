import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition'

type Props = {
  onNext: () => void
}

function Controls({ onNext }: Props) {
  // listening is true while the browser is recording; the other two flag unsupported browsers and a blocked mic
  const { listening, browserSupportsSpeechRecognition, isMicrophoneAvailable } =
    useSpeechRecognition()

  function handleMic() {
    if (listening) SpeechRecognition.stopListening()
    else SpeechRecognition.startListening()
  }

  return (
    <>
      {!browserSupportsSpeechRecognition && (
        <p>Speech recognition isn't supported in this browser. Try Chrome or Edge.</p>
      )}
      {!isMicrophoneAvailable && <p>Please allow the microphone to read aloud.</p>}
      <button className="mic" onClick={handleMic} disabled={!browserSupportsSpeechRecognition}>
        {listening ? 'Listening… click to stop' : 'Click to speak'}
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
