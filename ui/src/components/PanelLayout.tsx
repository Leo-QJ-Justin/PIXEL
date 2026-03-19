import { useCallback, useEffect, useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { useBridgeEvent } from '@/bridge/context'
import { TitleBar } from './TitleBar'
import { Sidebar } from './Sidebar'

const COLLAPSE_THRESHOLD = 500

export function PanelLayout() {
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)

  // Listen for Python-initiated navigation (tray menu clicks)
  useBridgeEvent(
    'window.navigateTo',
    useCallback(
      (data: { route: string }) => {
        navigate(data.route)
      },
      [navigate],
    ),
  )

  // Collapse sidebar when window is narrow
  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setCollapsed(entry.contentRect.width < COLLAPSE_THRESHOLD)
      }
    })
    observer.observe(document.body)
    return () => observer.disconnect()
  }, [])

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      <TitleBar />
      <div className="flex flex-1 min-h-0">
        <Sidebar collapsed={collapsed} />
        <main className="flex-1 overflow-y-auto min-h-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
