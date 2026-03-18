import { useCallback, useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'

interface WeekGridProps {
  habits: Array<{ id: string; title: string; icon: string }>
}

function getWeekStart(d: Date): string {
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  const monday = new Date(d)
  monday.setDate(diff)
  return monday.toISOString().split('T')[0]
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function WeekGrid({ habits }: WeekGridProps) {
  const { send } = useBridge()
  const [weekOffset, setWeekOffset] = useState(0)
  const [completions, setCompletions] = useState<Record<string, string[]>>({})

  const currentDate = new Date()
  currentDate.setDate(currentDate.getDate() + weekOffset * 7)
  const weekStart = getWeekStart(currentDate)

  useEffect(() => {
    send('habits.week', { week_start: weekStart })
  }, [send, weekStart])

  useBridgeEvent('habits.weekResult', useCallback((data: { completions: Record<string, string[]> }) => {
    setCompletions(data.completions)
  }, []))

  // Generate dates for the week
  const weekDates: string[] = []
  const ws = new Date(weekStart + 'T00:00:00')
  for (let i = 0; i < 7; i++) {
    const d = new Date(ws)
    d.setDate(ws.getDate() + i)
    weekDates.push(d.toISOString().split('T')[0])
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Week navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setWeekOffset(o => o - 1)}
          className="text-text-muted hover:text-primary transition-colors cursor-pointer"
        >
          <ChevronLeft size={18} />
        </button>
        <span className="text-sm font-heading font-semibold text-text">
          Week of {weekStart}
        </span>
        <button
          onClick={() => setWeekOffset(o => Math.min(o + 1, 0))}
          className="text-text-muted hover:text-primary transition-colors cursor-pointer"
          disabled={weekOffset >= 0}
        >
          <ChevronRight size={18} />
        </button>
      </div>

      {/* Grid header */}
      <div className="grid gap-1" style={{ gridTemplateColumns: 'auto repeat(7, 1fr)' }}>
        <div />
        {DAYS.map(day => (
          <div key={day} className="text-xs text-text-muted text-center font-medium">
            {day}
          </div>
        ))}

        {/* Habit rows */}
        {habits.map(habit => {
          const habitCompletions = completions[habit.id] || []
          return (
            <div key={habit.id} className="contents">
              <div className="flex items-center gap-1.5 pr-2 py-1">
                <span className="text-sm">{habit.icon}</span>
                <span className="text-xs text-text truncate">{habit.title}</span>
              </div>
              {weekDates.map(d => {
                const done = habitCompletions.includes(d)
                return (
                  <div key={d} className="flex items-center justify-center py-1">
                    <div
                      className={`w-4 h-4 rounded-full ${
                        done ? 'bg-primary' : 'bg-border'
                      }`}
                    />
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )
}
