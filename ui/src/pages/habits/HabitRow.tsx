import { motion } from 'framer-motion'
import { Check, Trash2 } from 'lucide-react'
import { useBridge } from '@/bridge/context'
import { cn } from '@/lib/utils'

interface HabitRowProps {
  habit: {
    id: string
    title: string
    icon: string
    frequency: string
    completed_today: boolean
    streak: number
    week_progress: number
    week_target: number
  }
}

export function HabitRow({ habit }: HabitRowProps) {
  const { send } = useBridge()

  function handleToggle() {
    if (habit.completed_today) {
      send('habits.uncomplete', { id: habit.id })
    } else {
      send('habits.complete', { id: habit.id })
    }
  }

  const showWeekProgress = habit.frequency === 'x_per_week'

  return (
    <motion.div
      layout
      className={cn(
        'group flex items-center gap-3 bg-surface border border-border rounded-default p-3 transition-colors',
        habit.completed_today && 'opacity-60',
      )}
    >
      <span className="text-lg shrink-0">{habit.icon}</span>

      <div className="flex-1 min-w-0">
        <p className={cn('text-sm text-text', habit.completed_today && 'line-through text-text-muted')}>
          {habit.title}
        </p>
        {showWeekProgress && (
          <div className="flex items-center gap-2 mt-1">
            <div className="h-1.5 flex-1 bg-border rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${Math.min(100, (habit.week_progress / habit.week_target) * 100)}%` }}
              />
            </div>
            <span className="text-xs text-text-muted shrink-0">
              {habit.week_progress}/{habit.week_target}
            </span>
          </div>
        )}
      </div>

      {habit.streak > 0 && (
        <span className="text-xs px-1.5 py-0.5 rounded bg-surface-hover text-primary shrink-0">
          🔥 {habit.streak}
        </span>
      )}

      <button
        onClick={handleToggle}
        className={cn(
          'w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors cursor-pointer',
          habit.completed_today
            ? 'bg-primary border-primary'
            : 'border-border hover:border-primary',
        )}
      >
        {habit.completed_today && <Check size={14} className="text-white" />}
      </button>

      <button
        onClick={() => send('habits.delete', { id: habit.id })}
        className="opacity-0 group-hover:opacity-100 transition-opacity text-text-muted hover:text-destructive cursor-pointer"
      >
        <Trash2 size={14} />
      </button>
    </motion.div>
  )
}
