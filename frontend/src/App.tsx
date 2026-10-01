import { Fragment } from 'react'
import './App.css'

type WordStatus = 'neutral' | 'correct' | 'retry'

const words: { text: string; status: WordStatus }[] = [
  { text: 'The', status: 'neutral' },
  { text: 'ship', status: 'correct' },
  { text: 'sank', status: 'correct' },
  { text: 'in', status: 'neutral' },
  { text: 'the', status: 'neutral' },
  { text: 'shell', status: 'retry' },
  { text: 'shop.', status: 'neutral' },
]

function App() {
  return (
    <main className="screen">
      <header className="top-bar">
        <button className="btn home" onClick={() => console.log('Home')}>
          Home
        </button>
        <h1 className="title">StoryWeave</h1>
      </header>

      <section className="reader">
        <p className="sentence">
          {words.map((word, i) => (
            <Fragment key={i}>
              {i > 0 && ' '}
              <span className={`word ${word.status}`}>{word.text}</span>
            </Fragment>
          ))}
        </p>
        <p className="caption">
          Green = got it &nbsp; Yellow = try again later (soft tint, no sound,
          no pop-up)
        </p>
      </section>

      <section className="controls">
        <button className="btn" onClick={() => console.log('Hear it')}>
          Hear it
        </button>
        <div className="mic-wrap">
          <button className="mic" onClick={() => console.log('MIC')}>
            MIC
          </button>
          <span className="caption">Listening...</span>
        </div>
        <button className="btn" onClick={() => console.log('Next line')}>
          Next line
        </button>
      </section>
    </main>
  )
}

export default App
