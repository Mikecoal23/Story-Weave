import { useState } from 'react'
import LoginScreen from './login/LoginScreen'
import EntryScreen from './entry/EntryScreen'
import PinScreen from './pin/PinScreen'
import ChildPicker from './child-ui/ChildPicker'
import type { Child } from './api/types'
import { getChildren } from './api/children'
import ChildApp from './child-ui/ChildApp'
import ParentDashboard from './parent-dashboard/ParentDashboard'

type Screen = 'login' | 'entry' | 'parentPin' | 'parent' | 'childPicker' | 'childPin' | 'child'

// Temporary until the parent PIN comes from the caregiver profile
const PARENT_PIN = '1234'

function App() {
  const [screen, setScreen] = useState<Screen>('login')
  // The caregiver's children, loaded once after login
  const [childList, setChildList] = useState<Child[]>([])
  // The child who picked themselves; needed later for story generation and sessions
  const [child, setChild] = useState<Child | null>(null)

  async function loadChildren() {
    setChildList(await getChildren())
  }

  async function handleLogin() {
    await loadChildren()
    setScreen('entry')
  }

  if (screen === 'login') return <LoginScreen onSuccess={handleLogin} />
  if (screen === 'parentPin')
    return <PinScreen title="Enter parent PIN" expectedPin={PARENT_PIN} onSuccess={() => setScreen('parent')} />
  if (screen === 'parent') return <ParentDashboard childList={childList} onChildAdded={loadChildren} onLogout={() => setScreen('login')} />
  if (screen === 'childPicker')
    return (
      <ChildPicker
        childList={childList}
        onSelect={(c) => {
          setChild(c)
          setScreen('childPin')
        }}
      />
    )
  if (screen === 'childPin' && child)
    return <PinScreen kid title={`Hi ${child.name}! Enter your PIN`} expectedPin={child.pin} onSuccess={() => setScreen('child')} />
  if (screen === 'child' && child)
    return <ChildApp child={child} onSwitchReader={() => setScreen('childPicker')} />

  return (
    <EntryScreen
      onSelect={(role) => setScreen(role === 'parent' ? 'parentPin' : 'childPicker')}
    />
  )
}

export default App
