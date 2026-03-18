import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { BridgeProvider } from '@/bridge/context'
import { PanelLayout } from '@/components/PanelLayout'
import { JournalPage } from '@/pages/journal/JournalPage'
import { PomodoroPage } from '@/pages/pomodoro/PomodoroPage'
import { SettingsPage } from '@/pages/settings/SettingsPage'
import { HabitsPage } from '@/pages/habits/HabitsPage'
import { TasksPage } from '@/pages/tasks/TasksPage'
import { WorkspacesPage } from '@/pages/workspaces/WorkspacesPage'
import { ScreenTimePage } from '@/pages/screen-time/ScreenTimePage'

export default function App() {
  return (
    <BridgeProvider>
      <HashRouter>
        <Routes>
          <Route element={<PanelLayout />}>
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/journal" element={<JournalPage />} />
            <Route path="/pomodoro" element={<PomodoroPage />} />
            <Route path="/habits" element={<HabitsPage />} />
            <Route path="/screen-time" element={<ScreenTimePage />} />
            <Route path="/workspaces" element={<WorkspacesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/journal" replace />} />
          </Route>
        </Routes>
      </HashRouter>
    </BridgeProvider>
  )
}
