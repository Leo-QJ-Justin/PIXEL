import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { AppUsage, TimelineEntry, DailyTotal } from '@/bridge/types'
import { CategoryBar } from './CategoryBar'
import { TopApps } from './TopApps'
import { ActivityTimeline } from './ActivityTimeline'
import { WeeklyChart } from './WeeklyChart'
import { ChevronLeft, ChevronRight } from 'lucide-react'

function formatDuration(totalSeconds: number): string {
  const abs = Math.abs(totalSeconds)
  const h = Math.floor(abs / 3600)
  const m = Math.floor((abs % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

interface DayData {
  total_s: number
  comparison_s: number
  category_breakdown: Record<string, number>
  top_apps: AppUsage[]
  timeline: TimelineEntry[]
}

interface WeekData {
  daily_totals: DailyTotal[]
  avg_s: number
  total_s: number
  trend_s: number
  top_apps: AppUsage[]
}

export function ScreenTimePage() {
  const { send } = useBridge()
  const [view, setView] = useState<'day' | 'week'>('day')
  const [dayOffset, setDayOffset] = useState(0)
  const [dayData, setDayData] = useState<DayData | null>(null)
  const [weekData, setWeekData] = useState<WeekData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const currentDate = new Date()
  currentDate.setDate(currentDate.getDate() + dayOffset)
  const dateStr = currentDate.toISOString().split('T')[0]
  const isToday = dayOffset === 0

  useEffect(() => {
    if (view === 'day') {
      send('screentime.today', { date: dateStr })
    } else {
      send('screentime.week', {})
    }
  }, [send, view, dateStr])

  useBridgeEvent('screentime.todayResult', useCallback((data: DayData) => {
    setDayData(data)
  }, []))

  useBridgeEvent('screentime.weekResult', useCallback((data: WeekData) => {
    setWeekData(data)
  }, []))

  useBridgeEvent('screentime.error', useCallback((data: { message: string }) => {
    setError(data.message)
    setTimeout(() => setError(null), 5000)
  }, []))

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col h-full p-4 gap-4"
    >
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-heading font-bold text-text">Screen Time</h1>
        <div className="flex bg-surface border border-border rounded-lg overflow-hidden">
          <button
            onClick={() => setView('day')}
            className={`text-xs px-3 py-1.5 transition-colors cursor-pointer ${
              view === 'day' ? 'bg-primary text-white' : 'text-text-muted hover:text-text'
            }`}
          >
            Day
          </button>
          <button
            onClick={() => setView('week')}
            className={`text-xs px-3 py-1.5 transition-colors cursor-pointer ${
              view === 'week' ? 'bg-primary text-white' : 'text-text-muted hover:text-text'
            }`}
          >
            Week
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</div>
      )}

      <div className="flex-1 overflow-y-auto space-y-4">
        {view === 'day' ? (
          <>
            {/* Date navigation */}
            <div className="flex items-center justify-between">
              <button onClick={() => setDayOffset(o => o - 1)} className="text-text-muted hover:text-primary cursor-pointer">
                <ChevronLeft size={18} />
              </button>
              <span className="text-sm font-heading font-semibold text-text">
                {isToday ? 'Today' : dateStr}
              </span>
              <button
                onClick={() => setDayOffset(o => Math.min(o + 1, 0))}
                className="text-text-muted hover:text-primary cursor-pointer"
                disabled={isToday}
              >
                <ChevronRight size={18} />
              </button>
            </div>

            {dayData ? (
              <>
                {/* Total */}
                <div className="bg-surface border border-border rounded-default p-4">
                  <div className="flex items-baseline gap-3">
                    <span className="text-2xl font-heading font-bold text-text">
                      {formatDuration(dayData.total_s)}
                    </span>
                    <span className={`text-xs ${dayData.comparison_s > 0 ? 'text-primary' : 'text-success'}`}>
                      {dayData.comparison_s > 0 ? '+' : ''}{formatDuration(Math.abs(dayData.comparison_s))} vs yesterday
                    </span>
                  </div>
                </div>

                <CategoryBar breakdown={dayData.category_breakdown} total={dayData.total_s} />
                <TopApps apps={dayData.top_apps} />
                <ActivityTimeline timeline={dayData.timeline} />
              </>
            ) : (
              <p className="text-sm text-text-muted text-center py-8">Loading...</p>
            )}
          </>
        ) : (
          <>
            {weekData ? (
              <>
                <div className="bg-surface border border-border rounded-default p-4">
                  <div className="flex items-baseline gap-3">
                    <span className="text-2xl font-heading font-bold text-text">
                      Avg {formatDuration(weekData.avg_s)}/day
                    </span>
                    <span className={`text-xs ${weekData.trend_s > 0 ? 'text-primary' : 'text-success'}`}>
                      {weekData.trend_s > 0 ? '+' : ''}{formatDuration(Math.abs(weekData.trend_s))} vs last week
                    </span>
                  </div>
                </div>

                <WeeklyChart dailyTotals={weekData.daily_totals} />
                <TopApps apps={weekData.top_apps} />
              </>
            ) : (
              <p className="text-sm text-text-muted text-center py-8">Loading...</p>
            )}
          </>
        )}
      </div>
    </motion.div>
  )
}
