import { useState } from 'react'
import { uploadLineAudio } from '../api/sessions'
import { useRecorder } from './useRecorder'

type Props = {
  sessionId: string | null
  lineNumber: number // 1-based, as the backend expects
  onNext: () => void
}

function Controls({ sessionId, lineNumber, onNext }: Props) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  // Runs when the recording stops: send the blob for scoring
  async function handleAudio(audio: Blob) {
    if (!sessionId) return
    setUploading(true)
    setError('')
    try {
      await uploadLineAudio(sessionId, lineNumber, audio)
    } catch {
      setError("We couldn't check that line. Try again.")
    }
    setUploading(false)
  }

  const { recording, micBlocked, supported, start, stop } = useRecorder(handleAudio)

  function handleMic() {
    if (recording) stop()
    else start()
  }

  return (
    <>
      {!supported && <p>Recording isn't supported in this browser. Try Chrome, Edge or Safari.</p>}
      {micBlocked && <p>Please allow the microphone to read aloud.</p>}
      {error && <p>{error}</p>}
      <button className="mic" onClick={handleMic} disabled={!supported || !sessionId || uploading}>
        {uploading ? 'Checking…' : recording ? 'Listening… click to stop' : 'Click to speak'}
      </button>
      <footer className="bottom-bar">
        <button className="btn btn-outline" onClick={() => console.log('Hear it')}>
          Hear it
        </button>
        <button className="btn btn-green" onClick={onNext} disabled={recording || uploading}>
          Next line
        </button>
      </footer>
    </>
  )
}

export default Controls
