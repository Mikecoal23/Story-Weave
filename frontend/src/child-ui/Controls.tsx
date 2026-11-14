import { useState } from 'react'
import { uploadLineAudio } from '../api/sessions'
import type { WordScore } from '../api/types'
import { useRecorder } from './useRecorder'

type Props = {
  sessionId: string | null
  lineNumber: number // 1-based, as the backend expects
  line: string
  tried: boolean // true once this line has been scored; "Hear it" waits for it so scores stay honest
  onScored: (scores: WordScore[]) => void
  onNext: () => void
}

function Controls({ sessionId, lineNumber, line, tried, onScored, onNext }: Props) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  // Runs when the recording stops: send the blob for scoring
  async function handleAudio(audio: Blob) {
    if (!sessionId) return
    setUploading(true)
    setError('')
    try {
      const response = await uploadLineAudio(sessionId, lineNumber, audio)
      onScored(response.result?.words ?? [])
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

  // Reads the line aloud with the browser's built-in voice
  function hearLine() {
    speechSynthesis.cancel() // stop any earlier line still being read
    const utterance = new SpeechSynthesisUtterance(line)
    utterance.rate = 0.8 // a little slower for early readers
    speechSynthesis.speak(utterance)
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
        {/* Off while recording or uploading, so the mic never scores the computer's voice */}
        <button className="btn btn-outline" onClick={hearLine} disabled={!tried || recording || uploading}>
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
