import { motion } from 'framer-motion'
import { Check, Trash2 } from 'lucide-react'
import { useBridge } from '@/bridge/context'
import { cn } from '@/lib/utils'
import type { Task } from '@/bridge/types'

interface TaskCardProps {
  task: Task
  subtasks: Task[]
}

export function TaskCard({ task, subtasks }: TaskCardProps) {
  const { send } = useBridge()

  const today = new Date().toISOString().split('T')[0]
  const isOverdue = task.due_date && task.due_date < today && !task.completed
  const isToday = task.due_date === today

  function handleToggle() {
    if (task.completed) {
      send('tasks.update', { id: task.id, title: task.title })
      // Uncomplete isn't in the bridge events, so we re-list
      send('tasks.list', { include_completed: true })
    } else {
      send('tasks.complete', { id: task.id })
    }
  }

  const completedSubtasks = subtasks.filter(s => s.completed).length

  return (
    <motion.div
      layout
      className={cn(
        'group flex items-start gap-3 bg-surface border border-border rounded-default p-3 transition-colors',
        task.completed && 'opacity-50',
      )}
    >
      {/* Checkbox */}
      <button
        onClick={handleToggle}
        className={cn(
          'mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors cursor-pointer',
          task.completed
            ? 'bg-primary border-primary'
            : 'border-border hover:border-primary',
        )}
      >
        {task.completed && <Check size={12} className="text-white" />}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={cn('text-sm text-text', task.completed && 'line-through text-text-muted')}>
          {task.title}
        </p>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          {task.tag && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-surface-hover text-primary">
              {task.tag}
            </span>
          )}
          {task.due_date && (
            <span className={cn(
              'text-xs px-1.5 py-0.5 rounded',
              isOverdue ? 'bg-destructive/10 text-destructive' :
              isToday ? 'bg-primary/10 text-primary' :
              'bg-surface-hover text-text-muted',
            )}>
              {task.due_date}
            </span>
          )}
          {subtasks.length > 0 && (
            <span className="text-xs text-text-muted">
              {completedSubtasks}/{subtasks.length} subtasks
            </span>
          )}
        </div>
      </div>

      {/* Delete */}
      <button
        onClick={() => send('tasks.delete', { id: task.id })}
        className="opacity-0 group-hover:opacity-100 transition-opacity text-text-muted hover:text-destructive cursor-pointer"
      >
        <Trash2 size={14} />
      </button>
    </motion.div>
  )
}
