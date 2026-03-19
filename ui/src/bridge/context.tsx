import { createContext, useContext, useEffect, useRef, type ReactNode } from 'react'
import { Bridge, type BridgeAPI } from './bridge'
import { MockBridge } from './mock'
import type { PyToJsEvents } from './types'

/* ── Context ────────────────────────────────────────────────────── */

const BridgeContext = createContext<BridgeAPI | null>(null)

/* ── Provider ───────────────────────────────────────────────────── */

function createBridge(): BridgeAPI {
  if (window.qt?.webChannelTransport) {
    return new Bridge()
  }
  console.log('[Bridge] No QWebChannel detected — using MockBridge')
  return new MockBridge()
}

// Singleton bridge instance, created once outside React lifecycle
const bridgeInstance = createBridge()

export function BridgeProvider({ children }: { children: ReactNode }) {
  return (
    <BridgeContext.Provider value={bridgeInstance}>
      {children}
    </BridgeContext.Provider>
  )
}

/* ── Hooks ──────────────────────────────────────────────────────── */

export function useBridge(): BridgeAPI {
  const ctx = useContext(BridgeContext)
  if (!ctx) {
    throw new Error('useBridge must be used within a BridgeProvider')
  }
  return ctx
}

export function useBridgeEvent<K extends keyof PyToJsEvents>(
  event: K,
  handler: (payload: PyToJsEvents[K]) => void,
): void {
  const { subscribe } = useBridge()
  // Keep handler ref stable to avoid stale closures
  const handlerRef = useRef(handler)
  useEffect(() => {
    handlerRef.current = handler
  })

  useEffect(() => {
    const unsubscribe = subscribe(event, (payload) => {
      handlerRef.current(payload)
    })
    return unsubscribe
  }, [subscribe, event])
}
