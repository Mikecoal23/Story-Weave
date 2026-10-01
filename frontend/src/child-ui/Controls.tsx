function Controls() {
  return (
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
  )
}

export default Controls
