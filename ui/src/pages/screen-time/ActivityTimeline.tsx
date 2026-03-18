const CATEGORY_DOT: Record<string, string> = {
  Productive: 'bg-success',
  Neutral: 'bg-border-hover',
  Distracting: 'bg-primary',
}

interface TimelineEntry {
  started_at: string
  display_name: string
  duration_s: number
  category: string
}

interface ActivityTimelineProps {
  timeline: Array<Record<string, unknown>>
}

export function ActivityTimeline({ timeline }: ActivityTimelineProps) {
  if (timeline.length === 0) return null

  const entries = timeline as unknown as TimelineEntry[]

  return (
    <div>
      <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide mb-2">
        Activity
      </h3>
      <div className="space-y-1">
        {entries.slice(0, 50).map((entry, i) => {
          const time = entry.started_at.split('T')[1]?.slice(0, 5) || ''
          const m = Math.floor(entry.duration_s / 60)
          const label = m > 0 ? `${m}m` : '<1m'
          return (
            <div key={i} className="flex items-center gap-2 py-0.5">
              <div className={`w-2 h-2 rounded-full shrink-0 ${CATEGORY_DOT[entry.category] || 'bg-border'}`} />
              <span className="text-[11px] text-text-muted w-10">{time}</span>
              <span className="text-[11px] text-text flex-1 truncate">{entry.display_name}</span>
              <span className="text-[11px] text-text-muted">{label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
