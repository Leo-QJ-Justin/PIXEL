import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { HabitWithStatus } from '@/bridge/types'

function getMondayOfWeek(d: Date): Date {
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  return new Date(d.getFullYear(), d.getMonth(), diff)
}

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

interface WeekGridProps {
  habits: HabitWithStatus[]
}

export function WeekGrid({ habits }: WeekGridProps) {
  const { send } = useBridge()
  const [weekOffset, setWeekOffset] = useState(0)
  const [completions, setCompletions] = useState<Record<string, string[]>>({})

  const monday = getMondayOfWeek(new Date())
  monday.setDate(monday.getDate() + weekOffset * 7)
  const weekStart = formatDate(monday)

  useEffect(() => {
    send('habits.week', { week_start: weekStart })
  }, [send, weekStart])

  useBridgeEvent('habits.weekResult', (data) => {
    setCompletions(data.completions)
  })

  const weekDates = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(d.getDate() + i)
    return formatDate(d)
  })

  return (
    <div className="rounded-lg border border-border bg-surface p-3">
      {/* Week nav */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={() => setWeekOffset(weekOffset - 1)}
          className="cursor-pointer p-1 text-text-muted hover:text-text"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-xs text-text-muted font-medium">
          {weekDates[0]} — {weekDates[6]}
        </span>
        <button
          onClick={() => setWeekOffset(Math.min(0, weekOffset + 1))}
          className="cursor-pointer p-1 text-text-muted hover:text-text"
          disabled={weekOffset >= 0}
        >
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[auto_repeat(7,1fr)] gap-1 text-center">
        <div />
        {DAY_LABELS.map((d) => (
          <span key={d} className="text-[10px] text-text-muted font-medium">
            {d}
          </span>
        ))}

        {/* Rows per habit */}
        {habits.map((habit) => (
          <div key={habit.id} className="contents">
            <span className="text-sm truncate pr-2 text-left flex items-center gap-1">
              <span>{habit.icon}</span>
              <span className="text-xs text-text-muted truncate">{habit.title}</span>
            </span>
            {weekDates.map((d) => {
              const done = (completions[habit.id] || []).includes(d)
              return (
                <div key={d} className="flex items-center justify-center py-0.5">
                  <div
                    className={`w-4 h-4 rounded-full border ${
                      done
                        ? 'bg-primary border-primary'
                        : 'border-border'
                    }`}
                  />
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
