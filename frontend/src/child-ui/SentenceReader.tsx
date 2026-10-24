import { Fragment } from 'react'
import type { WordScore } from '../api/types'

type Props = {
  line: string
  scores: WordScore[] | null // null until the line has been read and scored
}

// How a scored word looks to the child (Open Question 14): mastered words turn mint
// ("read well"), shaky and missed words turn coral ("try again").
function colorClass(score: WordScore | undefined) {
  if (!score) return ''
  return score.status === 'mastered' ? ' correct' : ' retry'
}

// The backend scores the line split on spaces, so word i lines up with scores[i]
function SentenceReader({ line, scores }: Props) {
  return (
    <section className="reader">
      <h2 className="prompt">Read this sentence</h2>
      <p className="sentence">
        {line.split(' ').map((word, i) => (
          <Fragment key={i}>
            {i > 0 && ' '}
            <span className={`word${colorClass(scores?.[i])}`}>{word}</span>
          </Fragment>
        ))}
      </p>
    </section>
  )
}

export default SentenceReader
