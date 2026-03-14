import type { JsToPyEvents, PyToJsEvents, Settings, JournalEntry } from './types'
import type { BridgeAPI, SendFn, SubscribeFn } from './bridge'

/* ── Sample Data ────────────────────────────────────────────────── */

const SAMPLE_SETTINGS: Settings = {
  user_name: 'Pixel User',
  birthday: '1990-01-01',
  general: {
    launch_on_startup: false,
    language: 'en',
  },
  behaviors: {
    idle_roam: true,
    sound_effects: true,
    notifications: true,
  },
  personality_engine: {
    provider: 'openai',
    model: 'gpt-4o-mini',
    api_key: '',
  },
  integrations: {},
}

const today = new Date().toISOString().split('T')[0]
const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]

const SAMPLE_ENTRIES: JournalEntry[] = [
  {
    date: today,
    mode: 'freeform',
    mood: 'happy',
    raw_text: 'Had a great productive day working on the PIXEL project!',
    clean_text: 'Had a great productive day working on the PIXEL project!',
    prompt_used: "What made today meaningful?",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    date: yesterday,
    mode: 'prompted',
    mood: 'neutral',
    raw_text: 'Spent some time reflecting on goals and priorities.',
    clean_text: 'Spent some time reflecting on goals and priorities.',
    prompt_used: "What are you grateful for today?",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
  },
]

/* ── MockBridge ─────────────────────────────────────────────────── */

export class MockBridge implements BridgeAPI {
  private listeners = new Map<string, Set<(payload: unknown) => void>>()
  private timerInterval: ReturnType<typeof setInterval> | null = null

  private emit<K extends keyof PyToJsEvents>(
    event: K,
    payload: PyToJsEvents[K],
  ): void {
    const handlers = this.listeners.get(event)
    if (handlers) {
      handlers.forEach((h) => h(payload))
    }
  }

  private simulateTimer(seconds: number): void {
    if (this.timerInterval !== null) {
      clearInterval(this.timerInterval)
    }
    let remaining = seconds
    this.timerInterval = setInterval(() => {
      remaining -= 1
      this.emit('timer.tick', { remaining, total: seconds })
      if (remaining <= 0) {
        clearInterval(this.timerInterval!)
        this.timerInterval = null
        this.emit('timer.finished', undefined as void)
      }
    }, 1000)
  }

  send: SendFn = ((event: string, payload?: unknown) => {
    console.log(`[MockBridge] send: ${event}`, payload ?? '')

    setTimeout(() => {
      switch (event as keyof JsToPyEvents) {
        case 'settings.load':
          this.emit('settings.loaded', SAMPLE_SETTINGS)
          break

        case 'settings.save':
          this.emit('settings.saved', { success: true })
          break

        case 'journal.loadEntries':
          this.emit('journal.entriesLoaded', { entries: SAMPLE_ENTRIES })
          break

        case 'journal.loadStats':
          this.emit('journal.statsLoaded', {
            total_entries: 42,
            streak: 7,
            monthly_counts: {
              '2026-01': 15,
              '2026-02': 18,
              '2026-03': 9,
            },
          })
          break

        case 'journal.save': {
          const savePayload = payload as { entry: JournalEntry }
          this.emit('journal.saved', {
            success: true,
            date: savePayload?.entry?.date ?? today,
          })
          break
        }

        case 'journal.cleanup': {
          this.emit('journal.cleanedUp', { success: true })
          break
        }

        case 'journal.loadMonth': {
          const monthPayload = payload as { year: number; month: number }
          const entries: Record<string, JournalEntry> = {}
          SAMPLE_ENTRIES.forEach((entry) => {
            entries[entry.date] = entry
          })
          this.emit('journal.monthLoaded', {
            year: monthPayload?.year ?? new Date().getFullYear(),
            month: monthPayload?.month ?? new Date().getMonth() + 1,
            entries,
          })
          break
        }

        case 'journal.loadEntry': {
          const entryPayload = payload as { date: string }
          const found = SAMPLE_ENTRIES.find((e) => e.date === entryPayload?.date) ?? null
          this.emit('journal.entryLoaded', { entry: found })
          break
        }

        case 'journal.delete': {
          const deletePayload = payload as { date: string }
          this.emit('journal.deleted', {
            success: true,
            date: deletePayload?.date ?? today,
          })
          break
        }

        case 'timer.start': {
          const timerPayload = payload as { duration: number }
          const duration = timerPayload?.duration ?? 1500
          this.emit('pomodoro.state', {
            phase: 'focus',
            remaining: duration,
            total: duration,
            sessions_completed: 0,
          })
          this.simulateTimer(duration)
          break
        }

        case 'timer.pause':
          if (this.timerInterval !== null) {
            clearInterval(this.timerInterval)
            this.timerInterval = null
          }
          break

        case 'timer.skip':
          if (this.timerInterval !== null) {
            clearInterval(this.timerInterval)
            this.timerInterval = null
          }
          this.emit('pomodoro.state', {
            phase: 'idle',
            remaining: 0,
            total: 0,
            sessions_completed: 1,
          })
          this.emit('timer.finished', undefined as void)
          break

        case 'timer.startBreak': {
          const breakPayload = payload as { duration: number }
          const breakDuration = breakPayload?.duration ?? 300
          this.emit('pomodoro.state', {
            phase: 'break',
            remaining: breakDuration,
            total: breakDuration,
            sessions_completed: 0,
          })
          this.simulateTimer(breakDuration)
          break
        }

        case 'timer.skipBreak':
          if (this.timerInterval !== null) {
            clearInterval(this.timerInterval)
            this.timerInterval = null
          }
          this.emit('pomodoro.state', {
            phase: 'idle',
            remaining: 0,
            total: 0,
            sessions_completed: 0,
          })
          break

        default:
          console.log(`[MockBridge] unhandled event: ${event}`)
      }
    }, 50)
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
