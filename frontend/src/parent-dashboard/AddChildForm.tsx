import { useState } from 'react'
import { createChild } from '../api/children'
import type { Child } from '../api/types'

type Props = {
  onAdded: (child: Child) => void
  onCancel: () => void
}

function AddChildForm({ onAdded, onCancel }: Props) {
  const [name, setName] = useState('')
  // Typed as a comma-separated string, split into a list on submit
  const [interests, setInterests] = useState('')
  const [grade, setGrade] = useState('1')
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) {
      setError('Please enter a name')
      return
    }
    try {
      const child = await createChild({
        name: name.trim(),
        interests: interests
          .split(',')
          .map((i) => i.trim())
          .filter(Boolean),
        gradeLevel: Number(grade),
      })
      onAdded(child)
    } catch {
      setError("Couldn't add the child")
    }
  }

  return (
    <form className="pd-card pd-form" onSubmit={handleSubmit}>
      <h2 className="pd-heading">Add a child</h2>
      <label>
        Name
        <input className="pd-input" value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <label>
        Interests (separate with commas)
        <input
          className="pd-input"
          placeholder="dinosaurs, space"
          value={interests}
          onChange={(e) => setInterests(e.target.value)}
        />
      </label>
      <label>
        Grade (1-3)
        <input
          className="pd-input"
          type="number"
          // Same range as the backend's CreateChildRequest and ck_child_grade_level
          min={1}
          max={3}
          value={grade}
          onChange={(e) => setGrade(e.target.value)}
        />
      </label>
      {error && <p className="pd-hint">{error}</p>}
      <div className="pd-form-buttons">
        <button type="submit">Add child</button>
        <button type="button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}

export default AddChildForm
