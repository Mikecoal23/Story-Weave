import { Fragment } from 'react'

type Props = {
  line: string
}

// Word colors return once recordings are scored (needs the mic work)
function SentenceReader({ line }: Props) {
  return (
    <section className="reader">
      <h2 className="prompt">Read this sentence</h2>
      <p className="sentence">
        {line.split(' ').map((word, i) => (
          <Fragment key={i}>
            {i > 0 && ' '}
            <span className="word">{word}</span>
          </Fragment>
        ))}
      </p>
    </section>
  )
}

export default SentenceReader
