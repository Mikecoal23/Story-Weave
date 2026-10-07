import { Fragment } from 'react'
import { words } from './constants'

function SentenceReader() {
  return (
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
  )
}

export default SentenceReader
