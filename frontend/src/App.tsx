import { useEffect, useState } from 'react'
import LoginScreen from './login/LoginScreen'
import EntryScreen from './entry/EntryScreen'
import PinScreen from './pin/PinScreen'
import ForgotPin from './pin/ForgotPin'
import ChildPicker from './child-ui/ChildPicker'
import type { Child } from './api/types'
import { getChildren, verifyChildPin } from './api/children'
import {
  getCaregiverId,
  hasCaregiverPin,
  logout,
  setCaregiverPin,
  verifyCaregiverPin,
} from './api/caregivers'
import ChildApp from './child-ui/ChildApp'
import ParentDashboard from './parent-dashboard/ParentDashboard'

type Screen = 'login' | 'entry' | 'parentPin' | 'forgotPin' | 'parent' | 'childPicker' | 'childPin' | 'child'

function App() {
  const [screen, setScreen] = useState<Screen>('login')
  // The caregiver's children, loaded once after login
  const [childList, setChildList] = useState<Child[]>([])
  // The child who picked themselves; needed later for story generation and sessions
  const [child, setChild] = useState<Child | null>(null)
  const [parentPinSet, setParentPinSet] = useState(false)
  // Shown on the login screen when the children can't be loaded (e.g. backend not running)
  const [loadError, setLoadError] = useState('')

  // After a page refresh: if a caregiver is still saved, skip the login screen
  useEffect(() => {
    if (!getCaregiverId()) return
    getChildren()
      .then((list) => {
        setChildList(list)
        setParentPinSet(hasCaregiverPin())
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
        onBack={() => {
          // Undo a "Forgot PIN?" reset that was started but not finished
          setParentPinSet(hasCaregiverPin())
          setScreen('entry')
        }}
        onForgot={parentPinSet ? () => setScreen('forgotPin') : undefined}
      />
    )
  if (screen === 'forgotPin')
    return (
      <ForgotPin
        // Treating the PIN as not set makes the PIN screen show "Set parent PIN" and save the new one
        onVerified={() => {
          setParentPinSet(false)
          setScreen('parentPin')
        }}
        onBack={() => setScreen('parentPin')}
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
        onSubmit={(pin) => verifyChildPin(child.id, pin)}
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
