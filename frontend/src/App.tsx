import { useEffect, useState } from 'react'
import LoginScreen from './login/LoginScreen'
import EntryScreen from './entry/EntryScreen'
import PinScreen from './pin/PinScreen'
import ChildPicker from './child-ui/ChildPicker'
import type { Child } from './api/types'
import { getChildren } from './api/children'
import { getCaregiverId, logout } from './api/caregivers'
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
  // Shown on the login screen when the children can't be loaded (e.g. backend not running)
  const [loadError, setLoadError] = useState('')

  // After a page refresh: if a caregiver is still saved, skip the login screen
  useEffect(() => {
    if (!getCaregiverId()) return
    getChildren()
      .then((list) => {
        setChildList(list)
        setScreen('entry')
      })
      .catch(() => setLoadError("Couldn't load your children. Is the backend running?"))
  }, [])

  async function loadChildren() {
    setChildList(await getChildren())
  }

  async function handleLogin() {
    try {
      await loadChildren()
    } catch {
      setLoadError("Couldn't load your children. Is the backend running?")
      return
    }
    setLoadError('')
    setScreen('entry')
  }

  // Forget the caregiver and their children, so the next login starts clean
  function handleLogout() {
    logout()
    setChildList([])
    setChild(null)
    setScreen('login')
  }

  if (screen === 'login') return <LoginScreen onSuccess={handleLogin} loadError={loadError} />
  if (screen === 'parentPin')
    return (
      <PinScreen
        title="Enter parent PIN"
        expectedPin={PARENT_PIN}
        onSuccess={() => setScreen('parent')}
        onBack={() => setScreen('entry')}
      />
    )
  if (screen === 'parent')
    return (
      <ParentDashboard
        childList={childList}
        onChildrenChanged={loadChildren}
        onSwitchUser={() => setScreen('entry')}
        onLogout={handleLogout}
      />
    )
  if (screen === 'childPicker')
    return (
      <ChildPicker
        childList={childList}
        onSelect={(c) => {
          setChild(c)
          setScreen('childPin')
        }}
        onBack={() => setScreen('entry')}
      />
    )
  if (screen === 'childPin' && child)
    return (
      <PinScreen
        kid
        title={`Hi ${child.name}! Enter your PIN`}
        expectedPin={child.pin}
        onSuccess={() => setScreen('child')}
        onBack={() => setScreen('childPicker')}
      />
    )
  if (screen === 'child' && child)
    return <ChildApp child={child} onSwitchReader={() => setScreen('childPicker')} />

  return (
    <EntryScreen
      onSelect={(role) => setScreen(role === 'parent' ? 'parentPin' : 'childPicker')}
    />
  )
}

export default App
