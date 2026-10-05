import './ParentDashboard.css'
import Sidebar from './Sidebar'
import WeekSummary from './WeekSummary'
import PatternsInProgress from './PatternsInProgress'
import TryAtHome from './TryAtHome'

function ParentDashboard() {
  return (
    <div className="pd-layout">
      <Sidebar />
      <main className="pd-main">
        <WeekSummary />
        <div className="pd-grid">
          <PatternsInProgress />
          <TryAtHome />
        </div>
      </main>
    </div>
  )
}

export default ParentDashboard
