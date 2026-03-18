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

export interface Task {
  id: string
  title: string
  notes: string | null
  completed: boolean
  due_date: string | null
  tag: string | null
  priority: 0 | 1 | 2 | 3  // 0=none, 1=low, 2=medium, 3=high
  parent_id: string | null
  sort_order: number
  created_at: string
  completed_at: string | null
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

/* ── Screen Time Types ─────────────────────────────────────────── */

export type ScreenTimeCategory = 'Productive' | 'Neutral' | 'Distracting'

export interface AppUsage {
  exe_name: string
  display_name: string
  total: number
  category: ScreenTimeCategory
}

export interface TimelineEntry {
  started_at: string
  ended_at: string
  display_name: string
  duration_s: number
  category: ScreenTimeCategory
}

export interface DailyTotal {
  date: string
  total_s: number
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

  'tasks.list': { include_completed?: boolean }
  'tasks.create': { title: string; due_date?: string; tag?: string; priority?: number; parent_id?: string; notes?: string }
  'tasks.update': { id: string; title?: string; notes?: string; due_date?: string | null; tag?: string | null; priority?: number }
  'tasks.complete': { id: string }
  'tasks.uncomplete': { id: string }
  'tasks.delete': { id: string }
  'tasks.reorder': { task_ids: string[] }

  'habits.list': { include_archived?: boolean }
  'habits.today': void
  'habits.complete': { id: string }
  'habits.uncomplete': { id: string }
  'habits.create': {
    title: string
    icon?: string
    frequency?: 'daily' | 'weekly' | 'x_per_week'
    target_count?: number
    reminder_time?: string
  }
  'habits.update': { id: string; [key: string]: unknown }
  'habits.delete': { id: string }
  'habits.stats': { id: string }
  'habits.week': { week_start: string }

  'workspaces.list': void
  'workspaces.create': { name: string; icon?: string; description?: string; color?: string; behavior?: string }
  'workspaces.update': { id: string; name?: string; description?: string; icon?: string; color?: string; behavior?: string }
  'workspaces.delete': { id: string }
  'workspaces.addItem': { workspace_id: string; type: string; path: string; display_name: string }
  'workspaces.removeItem': { workspace_id: string; item_id: string }
  'workspaces.launch': { id: string }
  'workspaces.browseFile': void
  'workspaces.browseFolder': void

  'screentime.today': { date?: string }
  'screentime.week': { week_start?: string }
  'screentime.categories': void
  'screentime.updateCategory': { exe_name: string; category: string; display_name?: string }
  'screentime.clear': void

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

  'tasks.listResult': { tasks: Task[] }
  'tasks.created': { task: Task }
  'tasks.updated': { task: Task }
  'tasks.completed': { task: Task }
  'tasks.deleted': { id: string }
  'tasks.reordered': Record<string, never>
  'tasks.error': { message: string }

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

  'workspaces.listResult': { workspaces: Record<string, unknown>[] }
  'workspaces.created': { workspace: Record<string, unknown> }
  'workspaces.updated': { workspace: Record<string, unknown> }
  'workspaces.deleted': { id: string }
  'workspaces.itemAdded': { workspace: Record<string, unknown> }
  'workspaces.itemRemoved': { workspace: Record<string, unknown> }
  'workspaces.launched': { success: boolean; errors?: string[] }
  'workspaces.browseFileResult': { path: string | null }
  'workspaces.browseFolderResult': { path: string | null }
  'workspaces.error': { message: string }

  'screentime.todayResult': { total_s: number; comparison_s: number; category_breakdown: Record<string, number>; top_apps: AppUsage[]; timeline: TimelineEntry[] }
  'screentime.weekResult': { daily_totals: DailyTotal[]; avg_s: number; total_s: number; trend_s: number; top_apps: AppUsage[] }
  'screentime.categoriesResult': { categories: AppUsage[] }
  'screentime.categoryUpdated': { category: AppUsage }
  'screentime.cleared': Record<string, never>
  'screentime.error': { message: string }

  'window.navigateTo': { route: string }
}
