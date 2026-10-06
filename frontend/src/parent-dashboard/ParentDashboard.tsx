import { useState } from 'react'
import './ParentDashboard.css'
import Sidebar, { type Tab } from './Sidebar'
import ChildPicker from './ChildPicker'
import ParentHome from './ParentHome'
import WeekSummary from './WeekSummary'
import PatternsInProgress from './PatternsInProgress'
import TryAtHome from './TryAtHome'

function ParentDashboard() {
  const [tab, setTab] = useState<Tab>('Home')
  // null = child picker; the name isn't used yet but will pick which child's data to load
  const [child, setChild] = useState<string | null>(null)

  if (child === null) return <ChildPicker onSelect={setChild} />

  return (
    <div className="pd-layout">
      <Sidebar active={tab} onSelect={setTab} />
      <main className="pd-main">
        {tab === 'Home' && <ParentHome />}
        {tab === 'Progress' && (
          <>
            <WeekSummary />
            <div className="pd-grid">
              <PatternsInProgress />
              <TryAtHome />
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default ParentDashboard
