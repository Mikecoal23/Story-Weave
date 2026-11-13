import { useEffect, useState } from 'react'
import './ParentDashboard.css'
import Sidebar, { type Tab } from './Sidebar'
import ParentHome from './ParentHome'
import WeekSummary from './WeekSummary'
import PatternsInProgress from './PatternsInProgress'
import TryAtHome from './TryAtHome'
import PracticeTab from './PracticeTab'
import { getDashboard } from '../api/dashboard'
import type { Child, Dashboard } from '../api/types'

type Props = {
  childList: Child[]
  onChildrenChanged: () => void // reloads the list in App after a child is added or removed
  onLogout: () => void
}

function ParentDashboard({ childList, onChildrenChanged, onLogout }: Props) {
  const [tab, setTab] = useState<Tab>('Home')
  // Defaults to the first child; the dropdown on Home switches it
  // Undefined when the caregiver has no children yet
  const [child, setChild] = useState<Child | undefined>(childList[0])
  // Bumping this re-runs the effect below, which is how "Try again" reloads the stats
  const [attempt, setAttempt] = useState(0)
  // The last fetch result, tagged with the child and attempt it belongs to (data null = failed)
  const [result, setResult] = useState<{ id: string; attempt: number; data: Dashboard | null } | null>(null)

  function handleAdded(newChild: Child) {
    onChildrenChanged()
    setChild(newChild)
  }

  // Select another child, or none (Home then shows "No readers yet")
  function handleRemoved(removed: Child) {
    onChildrenChanged()
    setChild(childList.find((c) => c.id !== removed.id))
  }

  // Reload the stats whenever a different child is selected
  const childId = child?.id
  // A result for another child or an older attempt counts as "still loading",
  // so the previous child's data never shows under the new name
  const current = result && result.id === childId && result.attempt === attempt ? result : null
  const dashboard = current?.data ?? null
  const failed = current !== null && current.data === null

  useEffect(() => {
    if (!childId) return
    let cancelled = false
    getDashboard(childId)
      .then((data) => {
        if (!cancelled) setResult({ id: childId, attempt, data })
      })
      .catch(() => {
        if (!cancelled) setResult({ id: childId, attempt, data: null })
      })
    return () => {
      cancelled = true
    }
  }, [childId, attempt])

  return (
    <div className="pd-layout">
      <Sidebar active={tab} onSelect={setTab} onLogout={onLogout} />
      <main className="pd-main">
        {tab === 'Home' && (
          <ParentHome
            child={child}
            childList={childList}
            onChange={setChild}
            onAdded={handleAdded}
            onRemoved={handleRemoved}
            dashboard={dashboard}
            failed={failed}
            onRetry={() => setAttempt(attempt + 1)}
          />
        )}
        {tab === 'Progress' &&
          (!child ? (
            <p className="pd-hint">Add a child on the Home tab first.</p>
          ) : dashboard ? (
            <>
              <WeekSummary childName={child.name} dashboard={dashboard} />
              <div className="pd-grid">
                <PatternsInProgress patterns={dashboard.patterns} />
                <TryAtHome words={dashboard.try_at_home} />
              </div>
            </>
          ) : failed ? (
            <>
              <p className="pd-hint">Couldn't load the dashboard</p>
              <button type="button" className="pd-chip" onClick={() => setAttempt(attempt + 1)}>
                Try again
              </button>
            </>
          ) : (
            <p className="pd-hint">Loading…</p>
          ))}
        {tab === 'Practice' && <PracticeTab />}
      </main>
    </div>
  )
}

export default ParentDashboard
