import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BookOpen, Pencil } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { JournalEntry } from '@/bridge/types'
import { CalendarMap } from './CalendarMap'
import { MoodTrend } from './MoodTrend'

interface StatsSurfaceProps {
  onOpenVault: () => void
  onWritePrompt: (prompt: string) => void
  onDateClick: (date: string) => void
}

const EMOJI_MAP: Record<string, string> = {
  happy: '😊',
  good: '🙂',
  neutral: '😐',
  sad: '😔',
  bad: '😢',
  '😊': '😊',
  '🙂': '🙂',
  '😐': '😐',
  '😔': '😔',
  '😢': '😢',
}

const FALLBACK_PROMPT = 'What is one thing you are grateful for today?'

export function StatsSurface({ onOpenVault, onWritePrompt, onDateClick }: StatsSurfaceProps) {
  const { send } = useBridge()

  const [stats, setStats] = useState<{
    total_entries: number
    streak: number
    monthly_counts: Record<string, number>
  } | null>(null)

  const [monthEntries, setMonthEntries] = useState<Record<string, JournalEntry>>({})
  const [prompt] = useState<string>(FALLBACK_PROMPT)

  // Current month/year for the request
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1

  useEffect(() => {
    send('journal.loadStats')
    send('journal.loadMonth', { year: currentYear, month: currentMonth })
  }, [send, currentYear, currentMonth])

  useBridgeEvent('journal.statsLoaded', (payload) => {
    setStats(payload)
  })

  useBridgeEvent('journal.monthLoaded', (payload) => {
    setMonthEntries(payload.entries)
  })

  // Build calendar data
  const entryDates = new Set(Object.keys(monthEntries))
  const moods: Record<string, string> = {}
  Object.entries(monthEntries).forEach(([date, entry]) => {
    if (entry.mood) {
      moods[date] = EMOJI_MAP[entry.mood] ?? entry.mood
    }
  })

  // Build mood trend from month entries (last 7)
  const moodTrendData = Object.entries(monthEntries)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-7)
    .map(([date, entry]) => ({
      date,
      mood: EMOJI_MAP[entry.mood] ?? entry.mood,
    }))
    .filter(({ mood }) => mood)

  // This month count
  const thisMonthKey = `${currentYear}-${String(currentMonth).padStart(2, '0')}`
  const thisMonth = stats?.monthly_counts[thisMonthKey] ?? Object.keys(monthEntries).length

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col gap-4 p-4 min-h-full"
    >
      {/* Heading */}
      <h1 className="font-heading text-xl font-bold text-text">Journal</h1>

      {/* Calendar heatmap */}
      <div className="bg-surface border border-border rounded-default p-3">
        <CalendarMap
          entryDates={entryDates}
          moods={moods}
          onDateClick={onDateClick}
        />
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Streak" value={`${stats?.streak ?? 0}`} unit="days" />
        <StatCard label="This Month" value={`${thisMonth}`} unit="entries" />
        <StatCard label="Total" value={`${stats?.total_entries ?? 0}`} unit="entries" />
      </div>

      {/* Mood trend */}
      <div className="bg-surface border border-border rounded-default p-3">
        <p className="text-xs text-text-muted mb-3 font-medium">Mood this month</p>
        <MoodTrend data={moodTrendData} />
      </div>

      {/* Daily prompt */}
      <div className="bg-surface border border-border rounded-default p-4 flex items-start gap-3">
        <Pencil size={16} className="text-primary mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-text-muted mb-1 font-medium">Today's prompt</p>
          <p className="text-sm text-text leading-snug">{prompt}</p>
          <button
            onClick={() => onWritePrompt(prompt)}
            className="cursor-pointer mt-2 text-xs text-primary font-medium hover:underline transition-colors"
          >
            Write about it →
          </button>
        </div>
      </div>

      {/* Open vault */}
      <button
        onClick={onOpenVault}
        className="cursor-pointer flex items-center justify-center gap-2 w-full py-3 rounded-default bg-primary text-white font-medium text-sm hover:bg-primary-hover transition-colors"
      >
        <BookOpen size={16} />
        Open Vault
      </button>
    </motion.div>
  )
}

interface StatCardProps {
  label: string
  value: string
  unit: string
}

function StatCard({ label, value, unit }: StatCardProps) {
  return (
    <div className="bg-surface border border-border rounded-default p-3 flex flex-col items-center gap-0.5">
      <span className="font-heading text-xl text-primary">{value}</span>
      <span className="text-[10px] text-text-muted text-center leading-tight">{unit}</span>
      <span className="text-[10px] text-text-muted text-center leading-tight">{label}</span>
    </div>
  )
}
