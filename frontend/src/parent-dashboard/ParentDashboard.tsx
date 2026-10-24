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
  onChildAdded: () => void // reloads the list in App after a child is created
  onLogout: () => void
}

function ParentDashboard({ childList, onChildAdded, onLogout }: Props) {
  const [tab, setTab] = useState<Tab>('Home')
  // Defaults to the first child; the dropdown on Home switches it
  const [child, setChild] = useState(childList[0])
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [failed, setFailed] = useState(false)

  function handleAdded(newChild: Child) {
    onChildAdded()
    setChild(newChild)
  }

  // Reload the stats whenever a different child is selected
  useEffect(() => {
    let cancelled = false
    getDashboard(child.id)
      .then((data) => {
        if (cancelled) return
        setDashboard(data)
        setFailed(false)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })
    return () => {
      cancelled = true
    }
  }, [child.id])

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
            dashboard={dashboard}
            failed={failed}
          />
        )}
        {tab === 'Progress' &&
          (dashboard ? (
            <>
              <WeekSummary dashboard={dashboard} />
              <div className="pd-grid">
                <PatternsInProgress patterns={dashboard.patterns} />
                <TryAtHome words={dashboard.tryAtHome} />
              </div>
            </>
          ) : (
            <p className="pd-hint">{failed ? "Couldn't load the dashboard" : 'Loading…'}</p>
          ))}
        {tab === 'Practice' && <PracticeTab />}
      </main>
    </div>
  )
}

export default ParentDashboard
