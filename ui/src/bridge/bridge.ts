import type { JsToPyEvents, PyToJsEvents } from './types'

/* ── Global type declarations for QWebChannel ───────────────────── */

interface QWebChannelTransport {
  send(data: string): void
  onmessage: ((data: { data: string }) => void) | null
}

interface QWebChannelObject {
  eventDispatched: {
    connect(cb: (name: string, payload: string) => void): void
    disconnect(cb: (name: string, payload: string) => void): void
  }
  receiveFromJs(event: string, payload: string): void
}

declare class QWebChannel {
  constructor(
    transport: QWebChannelTransport,
    callback: (channel: { objects: { bridge: QWebChannelObject } }) => void,
  )
}

declare global {
  interface Window {
    qt?: { webChannelTransport: QWebChannelTransport }
    QWebChannel?: typeof QWebChannel
  }
}

/* ── Bridge Types ───────────────────────────────────────────────── */

export type SendFn = <K extends keyof JsToPyEvents>(
  event: K,
  ...args: JsToPyEvents[K] extends void ? [] : [payload: JsToPyEvents[K]]
) => void

export type SubscribeFn = <K extends keyof PyToJsEvents>(
  event: K,
  handler: (payload: PyToJsEvents[K]) => void,
) => () => void

export interface BridgeAPI {
  send: SendFn
  subscribe: SubscribeFn
}

/* ── Real QWebChannel Bridge ────────────────────────────────────── */

export class Bridge implements BridgeAPI {
  private channel: QWebChannelObject | null = null
  private listeners = new Map<string, Set<(payload: unknown) => void>>()
  private ready: Promise<void>

  constructor() {
    this.ready = this.connect()
  }

  private connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const qt = window.qt
      if (!qt?.webChannelTransport) {
        reject(new Error('QWebChannel transport not available'))
        return
      }

      const WC = window.QWebChannel
      if (!WC) {
        reject(new Error('QWebChannel class not available'))
        return
      }

      new WC(qt.webChannelTransport, (channel) => {
        const bridge = channel.objects.bridge
        this.channel = bridge

        this.channel.eventDispatched.connect((name: string, payload: string) => {
          const handlers = this.listeners.get(name)
          if (handlers) {
            const parsed = payload ? JSON.parse(payload) : undefined
            handlers.forEach((h) => h(parsed))
          }
        })

        resolve()
      })
    })
  }

  send: SendFn = (async (event: string, payload?: unknown) => {
    await this.ready
    this.channel!.receiveFromJs(event, JSON.stringify(payload ?? null))
  }) as SendFn

  subscribe: SubscribeFn = ((event: string, handler: (payload: unknown) => void) => {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(handler)

    return () => {
      this.listeners.get(event)?.delete(handler)
    }
  }) as SubscribeFn
}
