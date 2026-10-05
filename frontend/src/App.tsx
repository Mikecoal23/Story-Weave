import { useState } from 'react'
import EntryScreen from './entry/EntryScreen'
import ChildApp from './child-ui/ChildApp'
import ParentDashboard from './parent-dashboard/ParentDashboard.tsx'

function App() {
  // null = entry screen; picking a role switches to that interface
  const [role, setRole] = useState<'child' | 'parent' | null>(null)

  if (role === 'child') return <ChildApp />
  if (role === 'parent') return <ParentDashboard />
  return <EntryScreen onSelect={setRole} />
}

export default App
