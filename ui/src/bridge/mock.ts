import type { JsToPyEvents, PyToJsEvents, Settings, JournalEntry } from './types'
import type { BridgeAPI, SendFn, SubscribeFn } from './bridge'

/* ── Sample Data ────────────────────────────────────────────────── */

const SAMPLE_SETTINGS: Settings = {
  user_name: 'Pixel User',
  birthday: '1990-01-01',
  general: {
    always_on_top: true,
    start_minimized: false,
    start_on_boot: false,
    sprite_default_facing: 'right',
    speech_bubble: {
      enabled: true,
      duration_ms: 3000,
    },
  },
  behaviors: {
    wander: {
      wander_chance: 0.3,
      wander_interval_min_ms: 5000,
      wander_interval_max_ms: 15000,
    },
    wave: {
      greeting: 'Hello!',
    },
    idle_variety: {
      enabled: true,
      interval_min_ms: 20000,
      interval_max_ms: 60000,
      chance: 0.4,
      behaviors: ['look_around', 'yawn', 'chill', 'play_ball', 'crochet'],
    },
    sleep: {
      inactivity_timeout_ms: 60000,
      schedule_enabled: false,
      schedule_start: '22:00',
      schedule_end: '06:00',
    },
    time_periods: {
      enabled: true,
      check_interval_ms: 30000,
      periods: { morning: '06:00', afternoon: '12:00', night: '20:00' },
      greetings: { morning: 'Rise and shine!', afternoon: 'Lunch time~', night: 'Sleepy time~' },
    },
  },
  personality_engine: {
    enabled: false,
    provider: 'openai',
    model: 'gpt-4o-mini',
    api_key: '',
    endpoint: '',
  },
  integrations: {
    pomodoro: {
      enabled: true,
      work_duration_minutes: 25,
      short_break_minutes: 5,
      long_break_minutes: 15,
      auto_start: false,
      sound_enabled: true,
      sessions_per_cycle: 4,
    },
  },
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
  private mockRemaining = 0
  private mockCompleted = 0

  private emit<K extends keyof PyToJsEvents>(
    event: K,
    payload: PyToJsEvents[K],
  ): void {
    const handlers = this.listeners.get(event)
    if (handlers) {
      handlers.forEach((h) => h(payload))
    }
  }

  private simulateTimer(seconds: number, onFinishState: string): void {
    if (this.timerInterval !== null) {
      clearInterval(this.timerInterval)
    }
    this.mockRemaining = seconds
    this.timerInterval = setInterval(() => {
      this.mockRemaining -= 1
      this.emit('timer.tick', { remaining: this.mockRemaining })
      if (this.mockRemaining <= 0) {
        clearInterval(this.timerInterval!)
        this.timerInterval = null
        if (onFinishState === 'SESSION_COMPLETE') {
          this.mockCompleted += 1
          this.emit('timer.state', {
            state: 'SESSION_COMPLETE',
            context: { previous_state: 'FOCUS', remaining_seconds: 0, completed_in_cycle: this.mockCompleted },
          })
          this.emit('pomodoro.session', { completed: this.mockCompleted })
        } else {
          this.emit('timer.state', {
            state: 'IDLE',
            context: { previous_state: onFinishState, remaining_seconds: 0, completed_in_cycle: this.mockCompleted },
          })
        }
        this.emit('pomodoro.stats', {
          daily: { [today]: this.mockCompleted },
          streak: 3,
          total: 42 + this.mockCompleted,
          longest_streak: 7,
        })
      }
    }, 1000)
  }

  send: SendFn = ((event: string, payload?: unknown) => {
    console.log(`[MockBridge] send: ${event}`, payload ?? '')

    setTimeout(() => {
      switch (event as keyof JsToPyEvents) {
        case 'settings.load':
          this.emit('settings.data', SAMPLE_SETTINGS)
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
          const entries: Record<string, JournalEntry> = {}
          SAMPLE_ENTRIES.forEach((entry) => {
            entries[entry.date] = entry
          })
          this.emit('journal.monthLoaded', {
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
          this.emit('timer.state', {
            state: 'FOCUS',
            context: { previous_state: 'IDLE', remaining_seconds: 1500, completed_in_cycle: this.mockCompleted },
          })
          this.simulateTimer(1500, 'SESSION_COMPLETE')
          break
        }

        case 'timer.pause':
          if (this.timerInterval !== null) {
            clearInterval(this.timerInterval)
            this.timerInterval = null
          }
          this.emit('timer.state', {
            state: 'FOCUS',
            context: { previous_state: 'FOCUS', remaining_seconds: this.mockRemaining, completed_in_cycle: this.mockCompleted, paused: true },
          })
          break

        case 'timer.skip':
          if (this.timerInterval !== null) {
            clearInterval(this.timerInterval)
            this.timerInterval = null
          }
          this.mockCompleted += 1
          this.emit('timer.state', {
            state: 'SESSION_COMPLETE',
            context: { previous_state: 'FOCUS', remaining_seconds: 0, completed_in_cycle: this.mockCompleted },
          })
          this.emit('pomodoro.session', { completed: this.mockCompleted })
          this.emit('pomodoro.stats', {
            daily: { [today]: this.mockCompleted },
            streak: 3,
            total: 42 + this.mockCompleted,
            longest_streak: 7,
          })
          break

        case 'timer.startBreak': {
          const isLong = this.mockCompleted >= 4
          const breakDuration = isLong ? 900 : 300
          const breakState = isLong ? 'LONG_BREAK' : 'SHORT_BREAK'
          this.emit('timer.state', {
            state: breakState,
            context: { previous_state: 'SESSION_COMPLETE', remaining_seconds: breakDuration, completed_in_cycle: this.mockCompleted },
          })
          this.simulateTimer(breakDuration, breakState)
          break
        }

        case 'timer.skipBreak':
          if (this.timerInterval !== null) {
            clearInterval(this.timerInterval)
            this.timerInterval = null
          }
          this.emit('timer.state', {
            state: 'IDLE',
            context: { previous_state: 'SESSION_COMPLETE', remaining_seconds: 0, completed_in_cycle: this.mockCompleted },
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
