const CATEGORY_COLORS: Record<string, string> = {
  Productive: 'var(--color-success)',
  Neutral: 'var(--color-border)',
  Distracting: 'var(--color-primary)',
}

interface CategoryBarProps {
  breakdown: Record<string, number>
  total: number
}

export function CategoryBar({ breakdown, total }: CategoryBarProps) {
  if (total === 0) return null

  const categories = Object.entries(breakdown).sort((a, b) => b[1] - a[1])

  return (
    <div>
      {/* Stacked bar */}
      <div className="h-3 rounded-full overflow-hidden flex bg-border">
        {categories.map(([cat, seconds]) => (
          <div
            key={cat}
            style={{
              width: `${(seconds / total) * 100}%`,
              backgroundColor: CATEGORY_COLORS[cat] || 'var(--color-border)',
            }}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-2">
        {categories.map(([cat, seconds]) => {
          const h = Math.floor(seconds / 3600)
          const m = Math.floor((seconds % 3600) / 60)
          const label = h > 0 ? `${h}h ${m}m` : `${m}m`
          return (
            <div key={cat} className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CATEGORY_COLORS[cat] || 'var(--color-border)' }}
              />
              <span className="text-xs text-text-muted">{cat} {label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
