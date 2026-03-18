import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { BridgeProvider } from '@/bridge/context'
import { PanelLayout } from '@/components/PanelLayout'
import { JournalPage } from '@/pages/journal/JournalPage'
import { PomodoroPage } from '@/pages/pomodoro/PomodoroPage'
import { SettingsPage } from '@/pages/settings/SettingsPage'
import { PlaceholderPage } from '@/pages/PlaceholderPage'
import { TasksPage } from '@/pages/tasks/TasksPage'

export default function App() {
  return (
    <BridgeProvider>
      <HashRouter>
        <Routes>
          <Route element={<PanelLayout />}>
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/journal" element={<JournalPage />} />
            <Route path="/pomodoro" element={<PomodoroPage />} />
            <Route path="/habits" element={<PlaceholderPage />} />
            <Route path="/screen-time" element={<PlaceholderPage />} />
            <Route path="/workspaces" element={<PlaceholderPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/journal" replace />} />
          </Route>
        </Routes>
      </HashRouter>
    </BridgeProvider>
  )
}
