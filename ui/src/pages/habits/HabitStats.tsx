import { useEffect, useState } from 'react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { HabitWithStatus } from '@/bridge/types'

interface StatsData {
  streak: number
  longest_streak: number
  completion_rate: number
  total: number
}

interface HabitStatsProps {
  habits: HabitWithStatus[]
}

export function HabitStats({ habits }: HabitStatsProps) {
  const { send } = useBridge()
  const [statsMap, setStatsMap] = useState<Record<string, StatsData>>({})

  useEffect(() => {
    setStatsMap({})
    for (const habit of habits) {
      send('habits.stats', { id: habit.id })
    }
  }, [send, habits])

  useBridgeEvent('habits.statsResult', (data) => {
    const id = (data as StatsData & { id?: string }).id
    if (id) {
      setStatsMap((prev) => ({ ...prev, [id]: data }))
    }
  })

  if (habits.length === 0) {
    return <p className="text-center text-text-muted text-sm py-4">No habits to show stats for.</p>
  }

  return (
    <div className="flex flex-col gap-3">
      {habits.map((habit) => {
        const stats = statsMap[habit.id]
        return (
          <div
            key={habit.id}
            className="rounded-lg border border-border bg-surface p-3"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{habit.icon}</span>
              <span className="text-sm font-medium text-text">{habit.title}</span>
            </div>
            {stats ? (
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center">
                  <p className="text-lg font-bold text-primary">
                    {stats.streak > 0 ? `\uD83D\uDD25 ${stats.streak}` : '0'}
                  </p>
                  <p className="text-[10px] text-text-muted">Current Streak</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-text">{stats.longest_streak}</p>
                  <p className="text-[10px] text-text-muted">Longest Streak</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-text">
                    {Math.round(stats.completion_rate * 100)}%
                  </p>
                  <p className="text-[10px] text-text-muted">30-day Rate</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-text">{stats.total}</p>
                  <p className="text-[10px] text-text-muted">Total</p>
                </div>
              </div>
            ) : (
              <p className="text-xs text-text-muted text-center">Loading...</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
