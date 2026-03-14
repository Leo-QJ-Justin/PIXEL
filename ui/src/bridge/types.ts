/* ── Data Models ─────────────────────────────────────────────────── */

export interface JournalEntry {
  date: string
  mode: string
  mood: string
  raw_text: string
  clean_text: string
  prompt_used: string
  created_at: string
  updated_at: string
}

export interface IntegrationSettingsField {
  key: string
  label: string
  type: 'text' | 'password' | 'toggle' | 'select'
  options?: string[]
  default?: string | boolean
}

export interface IntegrationSettingsSchema {
  id: string
  label: string
  fields: IntegrationSettingsField[]
}

export interface Settings {
  user_name: string
  birthday: string
  general: {
    launch_on_startup: boolean
    language: string
  }
  behaviors: {
    idle_roam: boolean
    sound_effects: boolean
    notifications: boolean
  }
  personality_engine: {
    provider: string
    model: string
    api_key: string
  }
  integrations: Record<string, Record<string, string | boolean>>
}

/* ── JS → Python Events ─────────────────────────────────────────── */

export interface JsToPyEvents {
  'settings.load': void
  'settings.save': Settings
  'settings.integrationSchema': void

  'timer.start': { duration: number }
  'timer.pause': void
  'timer.skip': void
  'timer.startBreak': { duration: number }
  'timer.skipBreak': void

  'pomodoro.getState': void

  'journal.loadEntries': { limit?: number; offset?: number }
  'journal.loadStats': void
  'journal.save': { entry: JournalEntry }
  'journal.cleanup': { date: string }
  'journal.loadMonth': { year: number; month: number }
  'journal.loadEntry': { date: string }
  'journal.delete': { date: string }

  'panel.resize': { width: number; height: number }
  'panel.close': void
  'panel.navigate': { route: string }
}

/* ── Python → JS Events ─────────────────────────────────────────── */

export interface PyToJsEvents {
  'settings.loaded': Settings
  'settings.saved': { success: boolean }
  'settings.integrationSchemaLoaded': IntegrationSettingsSchema[]

  'timer.tick': { remaining: number; total: number }
  'timer.finished': void
  'timer.paused': { remaining: number }
  'timer.breakTick': { remaining: number; total: number }
  'timer.breakFinished': void

  'pomodoro.state': {
    phase: 'idle' | 'focus' | 'break'
    remaining: number
    total: number
    sessions_completed: number
  }

  'journal.entriesLoaded': { entries: JournalEntry[] }
  'journal.statsLoaded': {
    total_entries: number
    streak: number
    monthly_counts: Record<string, number>
  }
  'journal.saved': { success: boolean; date: string }
  'journal.cleanedUp': { success: boolean }
  'journal.monthLoaded': {
    year: number
    month: number
    entries: Record<string, JournalEntry>
  }
  'journal.entryLoaded': { entry: JournalEntry | null }
  'journal.deleted': { success: boolean; date: string }

  'panel.route': { route: string }
}
