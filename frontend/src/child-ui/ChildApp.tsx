import './ChildApp.css'
import TopBar from './TopBar'
import SentenceReader from './SentenceReader'
import Controls from './Controls'

function ChildApp() {
  return (
    <main className="screen">
      <TopBar />
      <SentenceReader />
      <Controls />
    </main>
  )
}

export default ChildApp
