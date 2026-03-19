import type { AppUsage } from '@/bridge/types'
import { formatDuration } from '@/lib/utils'

interface TopAppsProps {
  apps: AppUsage[]
}

const CATEGORY_BADGE: Record<string, string> = {
  Productive: 'bg-success/10 text-success',
  Neutral: 'bg-border text-text-muted',
  Distracting: 'bg-primary/10 text-primary',
}

export function TopApps({ apps }: TopAppsProps) {
  if (apps.length === 0) return null
  const maxTotal = apps[0]?.total || 1

  return (
    <div>
      <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide mb-2">
        Top Apps
      </h3>
      <div className="space-y-2">
        {apps.map(app => {
          const label = formatDuration(app.total)
          return (
            <div key={app.exe_name} className="flex items-center gap-3">
              <span className="text-sm text-text w-24 truncate">{app.display_name}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${CATEGORY_BADGE[app.category] || CATEGORY_BADGE.Neutral}`}>
                {app.category}
              </span>
              <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${(app.total / maxTotal) * 100}%` }}
                />
              </div>
              <span className="text-xs text-text-muted w-12 text-right">{label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
