import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { BridgeProvider } from '@/bridge/context'
import { JournalPage } from '@/pages/journal/JournalPage'

function Placeholder({ name }: { name: string }) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <h1 className="text-2xl font-heading text-text-muted">{name}</h1>
    </div>
  )
}

function App() {
  return (
    <BridgeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/journal" element={<JournalPage />} />
          <Route path="/settings" element={<Placeholder name="Settings" />} />
          <Route path="/pomodoro" element={<Placeholder name="Pomodoro" />} />
          <Route path="*" element={<Navigate to="/journal" replace />} />
        </Routes>
      </BrowserRouter>
    </BridgeProvider>
  )
}

export default App
