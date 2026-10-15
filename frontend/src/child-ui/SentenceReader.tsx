import { Fragment } from 'react'

type Props = {
  line: string
}

// Word colors return once recordings are scored (needs the mic work)
function SentenceReader({ line }: Props) {
  return (
    <section className="reader">
      <p className="sentence">
        {line.split(' ').map((word, i) => (
          <Fragment key={i}>
            {i > 0 && ' '}
            <span className="word">{word}</span>
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
