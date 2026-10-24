import { useRef, useState } from 'react'

// Chrome, Edge and Firefox record webm; Safari records mp4. Use the first one the browser supports.
const MIME_TYPES = ['audio/webm', 'audio/mp4']

// Records the mic with MediaRecorder and hands the finished audio blob to onStop.
export function useRecorder(onStop: (audio: Blob) => void) {
  const [recording, setRecording] = useState(false)
  const [micBlocked, setMicBlocked] = useState(false)
  const recorder = useRef<MediaRecorder | null>(null)

  // Feature detection: false in browsers with no MediaRecorder or no usable audio format
  const supported =
    typeof MediaRecorder !== 'undefined' && MIME_TYPES.some((t) => MediaRecorder.isTypeSupported(t))

  async function start() {
    if (!supported) return
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setMicBlocked(true)
      return
    }
    const chunks: Blob[] = []
    const mimeType = MIME_TYPES.find((t) => MediaRecorder.isTypeSupported(t))
    const mr = new MediaRecorder(stream, { mimeType })
    mr.ondataavailable = (e) => chunks.push(e.data)
    mr.onstop = () => {
      // Turn the mic off so the browser's recording indicator goes away
      stream.getTracks().forEach((track) => track.stop())
      onStop(new Blob(chunks, { type: mr.mimeType }))
    }
    mr.start()
    recorder.current = mr
    setMicBlocked(false)
    setRecording(true)
  }

  function stop() {
    recorder.current?.stop()
    setRecording(false)
  }

  return { recording, micBlocked, supported, start, stop }
}
