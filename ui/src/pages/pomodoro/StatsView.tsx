import { ChevronLeft, Flame, Trophy, Star } from 'lucide-react'
import { motion } from 'framer-motion'
import { WeeklyChart } from './WeeklyChart'

interface StatsViewProps {
  daily: Record<string, number>
  streak: number
  total: number
  longest_streak: number
  onBack: () => void
}

export function StatsView({ daily, streak, total, longest_streak, onBack }: StatsViewProps) {
  // Find best day
  let bestDay = ''
  let bestCount = 0
  for (const [date, count] of Object.entries(daily)) {
    if (count > bestCount) {
      bestCount = count
      bestDay = date
    }
  }

  const bestDayLabel = bestDay
    ? new Date(bestDay + 'T00:00:00').toLocaleDateString('en', {
        month: 'short',
        day: 'numeric',
      })
    : '--'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col gap-5 p-4"
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        <button
          onClick={onBack}
          className="cursor-pointer flex items-center gap-1 text-sm text-text-muted hover:text-primary transition-colors"
          aria-label="Go back"
        >
          <ChevronLeft size={18} />
          Back
        </button>
        <h2 className="text-lg font-heading font-bold text-text ml-1">Quest Log</h2>
      </div>

      {/* Weekly Chart */}
      <section className="bg-surface rounded-default border border-border p-3">
        <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide mb-2">
          This Week
        </h3>
        <WeeklyChart daily={daily} />
      </section>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-surface rounded-default border border-border p-3 flex items-center gap-2">
          <Flame size={18} className="text-primary" />
          <div>
            <p className="text-lg font-heading font-bold text-text">{streak}</p>
            <p className="text-xs text-text-muted">Day Streak</p>
          </div>
        </div>
        <div className="bg-surface rounded-default border border-border p-3 flex items-center gap-2">
          <Star size={18} className="text-amber-400" />
          <div>
            <p className="text-lg font-heading font-bold text-text">{total}</p>
            <p className="text-xs text-text-muted">Total Sessions</p>
          </div>
        </div>
        <div className="bg-surface rounded-default border border-border p-3 flex items-center gap-2">
          <Trophy size={18} className="text-amber-500" />
          <div>
            <p className="text-lg font-heading font-bold text-text">{longest_streak}</p>
            <p className="text-xs text-text-muted">Longest Streak</p>
          </div>
        </div>
        <div className="bg-surface rounded-default border border-border p-3 flex items-center gap-2">
          <Star size={18} className="text-primary" />
          <div>
            <p className="text-lg font-heading font-bold text-text">
              {bestCount > 0 ? bestCount : '--'}
            </p>
            <p className="text-xs text-text-muted">Best Day ({bestDayLabel})</p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
