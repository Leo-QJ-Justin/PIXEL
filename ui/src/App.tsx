import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { BridgeProvider } from '@/bridge/context'
import { JournalPage } from '@/pages/journal/JournalPage'
import { SettingsPage } from '@/pages/settings/SettingsPage'
import { PomodoroPage } from '@/pages/pomodoro/PomodoroPage'

function App() {
  return (
    <BridgeProvider>
      <HashRouter>
        <Routes>
          <Route path="/journal" element={<JournalPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/pomodoro" element={<PomodoroPage />} />
          <Route path="*" element={<Navigate to="/journal" replace />} />
        </Routes>
      </HashRouter>
    </BridgeProvider>
  )
}

export default App
