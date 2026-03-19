import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import {
  ListTodo,
  CheckCircle,
  Timer,
  BarChart3,
  BookOpen,
  ChevronRight,
} from 'lucide-react'

interface DashboardSummary {
  greeting: string
  weather: { temp: number; condition: string; city: string } | null
  calendar_next: { summary: string; start_time: string; minutes_until: number } | null
  tasks: { due_today: number; overdue: number } | null
  habits: { done: number; total: number; streak: number } | null
  pomodoro: { sessions_today: number; minutes_today: number } | null
  screen_time: { total_s: number; productive_pct: number; breakdown: Record<string, number> } | null
  journal: { written_today: boolean; streak: number; prompt: string } | null
}

function formatScreenTime(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

export function HomePage() {
  const { send } = useBridge()
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardSummary | null>(null)

  useEffect(() => {
    send('dashboard.loadSummary')
  }, [send])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useBridgeEvent('dashboard.summaryResult', useCallback((d: any) => {
    setData(d as DashboardSummary)
  }, []))

  const today = new Date()
  const dateStr = today.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col h-full p-4 gap-4 overflow-y-auto"
    >
      {/* Greeting */}
      <div>
        <h1 className="text-xl font-heading font-bold text-text">
          {data?.greeting ?? 'Hello'}, Leo 👋
        </h1>
        <p className="text-xs text-text-muted mt-0.5">
          {dateStr}
          {data?.weather && ` · ${data.weather.condition} ${data.weather.temp}°C`}
        </p>
      </div>

      {/* Next event banner */}
      {data?.calendar_next && (
        <div
          className="rounded-default p-3 text-white cursor-pointer"
          style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-hover))' }}
          onClick={() => navigate('/settings')}
        >
          <p className="text-[10px] uppercase tracking-wide opacity-80">Next up</p>
          <p className="text-sm font-heading font-bold mt-0.5">{data.calendar_next.summary}</p>
          <p className="text-xs opacity-80">
            {data.calendar_next.minutes_until > 0
              ? `in ${data.calendar_next.minutes_until} minutes`
              : `at ${data.calendar_next.start_time}`}
          </p>
        </div>
      )}

      {/* Two-column grid */}
      <div className="grid grid-cols-2 gap-3 flex-1">
        {/* Left column: actionable */}
        <div className="flex flex-col gap-3">
          {/* Tasks */}
          <SummaryCard
            icon={<ListTodo size={16} />}
            title="Tasks"
            onClick={() => navigate('/tasks')}
          >
            {data?.tasks ? (
              <>
                <p className="text-2xl font-heading font-bold text-primary">
                  {data.tasks.due_today}
                </p>
                <p className="text-[11px] text-text-muted">
                  due today
                  {data.tasks.overdue > 0 && (
                    <span className="text-destructive"> · {data.tasks.overdue} overdue</span>
                  )}
                </p>
              </>
            ) : (
              <p className="text-xs text-text-muted">No tasks yet</p>
            )}
          </SummaryCard>

          {/* Journal */}
          <SummaryCard
            icon={<BookOpen size={16} />}
            title="Journal"
            onClick={() => navigate('/journal')}
          >
            {data?.journal ? (
              data.journal.written_today ? (
                <>
                  <p className="text-lg font-heading font-bold text-success">✓ Written</p>
                  <p className="text-[11px] text-text-muted">{data.journal.streak} day streak</p>
                </>
              ) : (
                <>
                  <p className="text-[11px] text-text-muted italic leading-relaxed">
                    "{data.journal.prompt}"
                  </p>
                  <p className="text-[11px] text-primary mt-1">Write about it →</p>
                </>
              )
            ) : (
              <p className="text-xs text-text-muted">Start journaling</p>
            )}
          </SummaryCard>
        </div>

        {/* Right column: stats */}
        <div className="flex flex-col gap-3">
          {/* Habits */}
          <SummaryCard
            icon={<CheckCircle size={16} />}
            title="Habits"
            onClick={() => navigate('/habits')}
          >
            {data?.habits ? (
              <>
                <div className="flex items-baseline gap-1.5">
                  <p className="text-2xl font-heading font-bold text-primary">
                    {data.habits.done}/{data.habits.total}
                  </p>
                  {data.habits.streak > 0 && (
                    <span className="text-[11px] text-text-muted">🔥 {data.habits.streak}</span>
                  )}
                </div>
                <div className="h-1 bg-border rounded-full mt-1.5 overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${data.habits.total > 0 ? (data.habits.done / data.habits.total) * 100 : 0}%` }}
                  />
                </div>
              </>
            ) : (
              <p className="text-xs text-text-muted">No habits yet</p>
            )}
          </SummaryCard>

          {/* Focus */}
          <SummaryCard
            icon={<Timer size={16} />}
            title="Focus"
            onClick={() => navigate('/pomodoro')}
          >
            {data?.pomodoro ? (
              <>
                <p className="text-2xl font-heading font-bold text-primary">
                  {data.pomodoro.minutes_today}m
                </p>
                <p className="text-[11px] text-text-muted">
                  {data.pomodoro.sessions_today} session{data.pomodoro.sessions_today !== 1 ? 's' : ''} today
                </p>
              </>
            ) : (
              <p className="text-xs text-text-muted">Start focusing</p>
            )}
          </SummaryCard>

          {/* Screen Time */}
          <SummaryCard
            icon={<BarChart3 size={16} />}
            title="Screen Time"
            onClick={() => navigate('/screen-time')}
          >
            {data?.screen_time ? (
              <>
                <p className="text-2xl font-heading font-bold text-primary">
                  {formatScreenTime(data.screen_time.total_s)}
                </p>
                <div className="flex gap-0.5 mt-1.5 h-1 rounded-full overflow-hidden">
                  {data.screen_time.breakdown.Productive && (
                    <div className="bg-success h-full" style={{ width: `${(data.screen_time.breakdown.Productive / data.screen_time.total_s) * 100}%` }} />
                  )}
                  {data.screen_time.breakdown.Neutral && (
                    <div className="bg-border-hover h-full" style={{ width: `${(data.screen_time.breakdown.Neutral / data.screen_time.total_s) * 100}%` }} />
                  )}
                  {data.screen_time.breakdown.Distracting && (
                    <div className="bg-primary h-full" style={{ width: `${(data.screen_time.breakdown.Distracting / data.screen_time.total_s) * 100}%` }} />
                  )}
                </div>
                <p className="text-[11px] text-text-muted mt-0.5">{data.screen_time.productive_pct}% productive</p>
              </>
            ) : (
              <p className="text-xs text-text-muted">Tracking...</p>
            )}
          </SummaryCard>
        </div>
      </div>
    </motion.div>
  )
}

interface SummaryCardProps {
  icon: React.ReactNode
  title: string
  onClick: () => void
  children: React.ReactNode
}

function SummaryCard({ icon, title, onClick, children }: SummaryCardProps) {
  return (
    <button
      onClick={onClick}
      className="bg-surface border border-border rounded-default p-3 text-left transition-all hover:border-border-hover hover:shadow-sm cursor-pointer group"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <span className="text-text-muted">{icon}</span>
          <span className="text-[10px] font-heading font-semibold text-text-muted uppercase tracking-wide">{title}</span>
        </div>
        <ChevronRight size={12} className="text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
      {children}
    </button>
  )
}
