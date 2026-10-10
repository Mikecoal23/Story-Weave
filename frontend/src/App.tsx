import { useState } from 'react'
import LoginScreen from './login/LoginScreen'
import EntryScreen from './entry/EntryScreen'
import PinScreen from './pin/PinScreen'
import ChildPicker from './parent-dashboard/ChildPicker'
import { type Child } from './parent-dashboard/mockChildren'
import ChildApp from './child-ui/ChildApp'
import ParentDashboard from './parent-dashboard/ParentDashboard.tsx'

type Screen = 'login' | 'entry' | 'parentPin' | 'parent' | 'childPicker' | 'childPin' | 'child'

// Temporary until the parent PIN comes from the caregiver profile
const PARENT_PIN = '1234'

function App() {
  const [screen, setScreen] = useState<Screen>('login')
  // The child who picked themselves; needed later for story generation and sessions
  const [child, setChild] = useState<Child | null>(null)

  if (screen === 'login') return <LoginScreen onSuccess={() => setScreen('entry')} />
  if (screen === 'parentPin')
    return <PinScreen title="Enter parent PIN" expectedPin={PARENT_PIN} onSuccess={() => setScreen('parent')} />
  if (screen === 'parent') return <ParentDashboard onLogout={() => setScreen('login')} />
  if (screen === 'childPicker')
    return (
      <ChildPicker
        onSelect={(c) => {
          setChild(c)
          setScreen('childPin')
        }}
      />
    )
  if (screen === 'childPin' && child)
    return <PinScreen kid title={`Hi ${child.name}! Enter your PIN`} expectedPin={child.pin} onSuccess={() => setScreen('child')} />
  if (screen === 'child') return <ChildApp onSwitchReader={() => setScreen('childPicker')} />

  return (
    <EntryScreen
      onSelect={(role) => setScreen(role === 'parent' ? 'parentPin' : 'childPicker')}
    />
  )
}

export default App
