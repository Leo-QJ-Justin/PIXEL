import { cn } from '@/lib/utils'

interface MoodTrendProps {
  data: { date: string; mood: string }[]
}

const MOOD_ORDER = ['😢', '😔', '😐', '🙂', '😊']

function moodIndex(mood: string): number {
  const idx = MOOD_ORDER.indexOf(mood)
  return idx === -1 ? 2 : idx // default to neutral
}

function dayLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return ['S', 'M', 'T', 'W', 'T', 'F', 'S'][d.getDay()]
}

const BAR_MAX_HEIGHT = 40 // px

export function MoodTrend({ data }: MoodTrendProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-16 text-sm text-text-muted">
        No mood data yet
      </div>
    )
  }

  return (
    <div className="flex items-end gap-2 justify-center">
      {data.map(({ date, mood }) => {
        const idx = moodIndex(mood)
        const barHeight = Math.round(((idx + 1) / MOOD_ORDER.length) * BAR_MAX_HEIGHT)

        return (
          <div key={date} className="flex flex-col items-center gap-1">
            <span className="text-base leading-none">{mood}</span>
            <div
              className={cn('w-6 rounded-sm bg-primary/30 transition-all')}
              style={{ height: `${barHeight}px` }}
            />
            <span className="text-[10px] text-text-muted">{dayLabel(date)}</span>
          </div>
        )
      })}
    </div>
  )
}
