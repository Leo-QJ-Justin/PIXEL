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
    always_on_top: boolean
    start_minimized: boolean
    start_on_boot: boolean
    sprite_default_facing: string
    speech_bubble: {
      enabled: boolean
      duration_ms: number
    }
  }
  behaviors: {
    wander: {
      wander_chance: number
      wander_interval_min_ms: number
      wander_interval_max_ms: number
    }
    wave: {
      greeting: string
    }
    idle_variety: {
      enabled: boolean
      interval_min_ms: number
      interval_max_ms: number
      chance: number
      behaviors: string[]
    }
    sleep: {
      inactivity_timeout_ms: number
      schedule_enabled: boolean
      schedule_start: string
      schedule_end: string
    }
    time_periods: {
      enabled: boolean
      check_interval_ms: number
      periods: Record<string, string>
      greetings: Record<string, string>
    }
  }
  personality_engine: {
    enabled: boolean
    provider: string
    model: string
    api_key: string
    endpoint: string
  }
  integrations: {
    pomodoro: {
      enabled: boolean
      work_duration_minutes: number
      short_break_minutes: number
      long_break_minutes: number
      auto_start: boolean
      sound_enabled: boolean
      sessions_per_cycle: number
    }
    [key: string]: Record<string, unknown>
  }
}

export interface Habit {
  id: string
  title: string
  icon: string
  frequency: 'daily' | 'weekly' | 'x_per_week'
  target_count: number
  reminder_time: string | null
  sort_order: number
  created_at: string
  archived: boolean
}

export interface HabitWithStatus extends Habit {
  completed_today: boolean
  streak: number
  week_progress: number
  week_target: number
}

/* ── JS → Python Events ─────────────────────────────────────────── */

export interface JsToPyEvents {
  'settings.load': void
  'settings.save': { settings: Settings }
  'settings.integrationSchema': void

  'timer.start': void
  'timer.pause': void
  'timer.skip': void
  'timer.startBreak': void
  'timer.skipBreak': void

  'pomodoro.getState': void

  'journal.loadEntries': { limit?: number; offset?: number }
  'journal.loadStats': void
  'journal.save': { entry: JournalEntry; explicit?: boolean }
  'journal.cleanup': { text: string }
  'journal.loadMonth': { year: number; month: number }
  'journal.loadEntry': { date: string }
  'journal.delete': { date: string }
  'journal.editorOpened': void
  'journal.editorClosed': void

  'panel.resize': { width: number; height: number }
  'panel.close': void
  'panel.navigate': { route: string }

  'habits.list': { include_archived?: boolean }
  'habits.today': void
  'habits.complete': { id: string }
  'habits.uncomplete': { id: string }
  'habits.create': {
    title: string
    icon?: string
    frequency?: string
    target_count?: number
    reminder_time?: string
  }
  'habits.update': { id: string; [key: string]: unknown }
  'habits.delete': { id: string }
  'habits.stats': { id: string }
  'habits.week': { week_start: string }

  'window.navigate': { route: string }
  'window.minimize': void
  'window.maximize': void
  'window.close': void
  'window.dragStart': { x: number; y: number }
  'window.dragMove': { x: number; y: number }
  'window.dragEnd': void
}

/* ── Python → JS Events ─────────────────────────────────────────── */

export interface PyToJsEvents {
  'settings.data': Settings
  'settings.saved': { success: boolean }
  'settings.integrationSchemaLoaded': IntegrationSettingsSchema[]

  'timer.tick': { remaining: number }
  'timer.state': { state: string; context: Record<string, unknown> }
  'timer.finished': void
  'timer.paused': { remaining: number }
  'timer.breakTick': { remaining: number; total: number }
  'timer.breakFinished': void

  'pomodoro.session': { completed: number }
  'pomodoro.stats': {
    daily: Record<string, number>
    streak: number
    total: number
    longest_streak: number
  }
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
  'journal.saved': { success?: boolean; date?: string; id?: number; error?: boolean }
  'journal.cleanedUp': { success: boolean; cleanText?: string; error?: boolean }
  'journal.monthLoaded': {
    entries: Record<string, JournalEntry>
  }
  'journal.entryLoaded': { entry: JournalEntry | null }
  'journal.deleted': { success?: boolean; date?: string; error?: boolean }

  'panel.route': { route: string }

  'habits.listResult': { habits: Habit[] }
  'habits.todayResult': { habits: HabitWithStatus[] }
  'habits.completed': { habit: HabitWithStatus; milestone?: number }
  'habits.uncompleted': { habit: HabitWithStatus }
  'habits.created': { habit: Habit }
  'habits.updated': { habit: Habit }
  'habits.deleted': { id: string }
  'habits.statsResult': {
    id: string
    streak: number
    longest_streak: number
    completion_rate: number
    total: number
  }
  'habits.weekResult': { completions: Record<string, string[]> }
  'habits.error': { message: string }

  'window.navigateTo': { route: string }
}
