import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CalendarMapProps {
  entryDates: Set<string>
  moods: Record<string, string>
  onDateClick: (date: string) => void
}

const DAY_HEADERS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function toDateString(year: number, month: number, day: number): string {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

export function CalendarMap({ entryDates, moods, onDateClick }: CalendarMapProps) {
  const today = new Date()
  const todayStr = toDateString(today.getFullYear(), today.getMonth() + 1, today.getDate())

  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1) // 1-indexed

  const firstDay = new Date(year, month - 1, 1).getDay() // 0=Sun
  const daysInMonth = new Date(year, month, 0).getDate()

  const monthLabel = new Date(year, month - 1, 1).toLocaleString('default', {
    month: 'long',
    year: 'numeric',
  })

  function prevMonth() {
    if (month === 1) {
      setYear((y) => y - 1)
      setMonth(12)
    } else {
      setMonth((m) => m - 1)
    }
  }

  function nextMonth() {
    if (month === 12) {
      setYear((y) => y + 1)
      setMonth(1)
    } else {
      setMonth((m) => m + 1)
    }
  }

  // Build grid cells: leading empty cells + day cells
  const cells: (number | null)[] = [
    ...Array(firstDay).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]

  return (
    <div className="w-full">
      {/* Month navigation */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={prevMonth}
          className="cursor-pointer p-1 rounded-sm text-text-muted hover:text-primary hover:bg-surface transition-colors"
          aria-label="Previous month"
        >
          <ChevronLeft size={18} />
        </button>
        <span className="font-heading text-sm font-medium text-text">{monthLabel}</span>
        <button
          onClick={nextMonth}
          className="cursor-pointer p-1 rounded-sm text-text-muted hover:text-primary hover:bg-surface transition-colors"
          aria-label="Next month"
        >
          <ChevronRight size={18} />
        </button>
      </div>

      {/* Day-of-week headers */}
      <div className="grid grid-cols-7 mb-1">
        {DAY_HEADERS.map((d) => (
          <div key={d} className="text-center text-[10px] text-text-muted py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 gap-0.5">
        {cells.map((day, idx) => {
          if (day === null) {
            return <div key={`empty-${idx}`} />
          }

          const dateStr = toDateString(year, month, day)
          const hasEntry = entryDates.has(dateStr)
          const mood = moods[dateStr]
          const isToday = dateStr === todayStr

          return (
            <button
              key={dateStr}
              onClick={() => onDateClick(dateStr)}
              className={cn(
                'cursor-pointer h-8 w-full flex items-center justify-center text-xs rounded-sm transition-colors',
                hasEntry
                  ? 'bg-primary/20 text-primary font-medium hover:bg-primary/30'
                  : 'text-text-muted hover:bg-surface',
                isToday && 'ring-2 ring-accent',
              )}
              aria-label={dateStr}
            >
              {mood ? (
                <span className="text-base leading-none">{mood}</span>
              ) : (
                day
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
