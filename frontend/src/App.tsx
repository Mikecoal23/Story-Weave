import { useState } from 'react'
import LoginScreen from './login/LoginScreen'
import EntryScreen from './entry/EntryScreen'
import PinScreen from './pin/PinScreen'
import ChildPicker from './child-ui/ChildPicker'
import type { Child } from './api/types'
import { getChildren, verifyChildPin } from './api/children'
import {
  hasCaregiverPin,
  logout,
  setCaregiverPin,
  verifyCaregiverPin,
} from './api/caregivers'
import ChildApp from './child-ui/ChildApp'
import ParentDashboard from './parent-dashboard/ParentDashboard'

type Screen = 'login' | 'entry' | 'parentPin' | 'parent' | 'childPicker' | 'childPin' | 'child'

function App() {
  const [screen, setScreen] = useState<Screen>('login')
  // The caregiver's children, loaded once after login
  const [childList, setChildList] = useState<Child[]>([])
  // The child who picked themselves; needed later for story generation and sessions
  const [child, setChild] = useState<Child | null>(null)
  const [parentPinSet, setParentPinSet] = useState(false)
  // Shown on the login screen when the children can't be loaded (e.g. backend not running)
  const [loadError, setLoadError] = useState('')

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
    setParentPinSet(hasCaregiverPin())
    setLoadError('')
    setScreen('entry')
  }

  // Forget the caregiver and their children, so the next login starts clean
  function handleLogout() {
    logout()
    setChildList([])
    setChild(null)
    setParentPinSet(false)
    setScreen('login')
  }

  if (screen === 'login') return <LoginScreen onSuccess={handleLogin} loadError={loadError} />
  if (screen === 'parentPin')
    return (
      <PinScreen
        title={parentPinSet ? 'Enter parent PIN' : 'Set parent PIN'}
        onSubmit={async (pin) => {
          if (!parentPinSet) {
            await setCaregiverPin(pin)
            setParentPinSet(true)
            return true
          }
          return verifyCaregiverPin(pin)
        }}
        onSuccess={() => setScreen('parent')}
      />
    )
  if (screen === 'parent') return <ParentDashboard childList={childList} onChildrenChanged={loadChildren} onLogout={handleLogout} />
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
    return (
      <PinScreen
        kid
        title={`Hi ${child.name}! Enter your PIN`}
        onSubmit={(pin) => verifyChildPin(child.id, pin)}
        onSuccess={() => setScreen('child')}
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
