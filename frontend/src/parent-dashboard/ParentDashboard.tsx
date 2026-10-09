import { useState } from 'react'
import './ParentDashboard.css'
import Sidebar, { type Tab } from './Sidebar'
import { children } from './mockChildren'
import ParentHome from './ParentHome'
import WeekSummary from './WeekSummary'
import PatternsInProgress from './PatternsInProgress'
import TryAtHome from './TryAtHome'
import PracticeTab from './PracticeTab'

type Props = {
  onLogout: () => void
}

function ParentDashboard({ onLogout }: Props) {
  const [tab, setTab] = useState<Tab>('Home')
  // Defaults to the first child; the dropdown on Home switches it
  const [child, setChild] = useState(children[0])

  return (
    <div className="pd-layout">
      <Sidebar active={tab} onSelect={setTab} onLogout={onLogout} />
      <main className="pd-main">
        {tab === 'Home' && <ParentHome child={child} onChange={setChild} />}
        {tab === 'Progress' && (
          <>
            <WeekSummary />
            <div className="pd-grid">
              <PatternsInProgress />
              <TryAtHome />
            </div>
          </>
        )}
        {tab === 'Practice' && <PracticeTab />}
      </main>
    </div>
  )
}

export default ParentDashboard
