import { useCallback, useRef } from 'react'
import { Minus, Square, X } from 'lucide-react'
import { useBridge } from '@/bridge/context'

export function TitleBar() {
  const { send } = useBridge()
  const isDragging = useRef(false)

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if ((e.target as HTMLElement).closest('[data-window-button]')) return
      isDragging.current = true
      send('window.dragStart', { x: e.screenX, y: e.screenY })
    },
    [send],
  )

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging.current) return
      send('window.dragMove', { x: e.screenX, y: e.screenY })
    },
    [send],
  )

  const handleMouseUp = useCallback(() => {
    if (!isDragging.current) return
    isDragging.current = false
    send('window.dragEnd')
  }, [send])

  return (
    <div
      className="flex items-center h-9 px-3 select-none shrink-0"
      style={{
        background: 'linear-gradient(135deg, var(--color-surface-hover), var(--color-background))',
        borderBottom: '1px solid var(--color-border)',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Logo + title */}
      <div className="flex items-center gap-1.5">
        <div className="w-[18px] h-[18px] rounded-full bg-primary flex items-center justify-center text-[10px] font-bold text-white">
          P
        </div>
        <span className="text-xs font-heading font-semibold text-text">
          PIXEL
        </span>
      </div>

      {/* Window controls — dots with expanded hit areas */}
      <div className="ml-auto flex items-center gap-0.5">
        <button
          data-window-button
          onClick={() => send('window.minimize')}
          className="group w-7 h-7 flex items-center justify-center"
        >
          <span className="w-3 h-3 rounded-full bg-amber-400 transition-colors flex items-center justify-center">
            <Minus size={8} className="opacity-0 group-hover:opacity-100 transition-opacity text-amber-900" />
          </span>
        </button>
        <button
          data-window-button
          onClick={() => send('window.maximize')}
          className="group w-7 h-7 flex items-center justify-center"
        >
          <span className="w-3 h-3 rounded-full bg-green-400 transition-colors flex items-center justify-center">
            <Square size={7} className="opacity-0 group-hover:opacity-100 transition-opacity text-green-900" />
          </span>
        </button>
        <button
          data-window-button
          onClick={() => send('window.close')}
          className="group w-7 h-7 flex items-center justify-center"
        >
          <span className="w-3 h-3 rounded-full bg-destructive transition-colors flex items-center justify-center">
            <X size={8} className="opacity-0 group-hover:opacity-100 transition-opacity text-white" />
          </span>
        </button>
      </div>
    </div>
  )
}
