import { useCallback, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { Task } from '@/bridge/types'
import { TaskAddInput } from './TaskAddInput'
import { TaskCard } from './TaskCard'
import { TagFilter } from './TagFilter'

export function TasksPage() {
  const { send } = useBridge()
  const [tasks, setTasks] = useState<Task[]>([])
  const [activeTag, setActiveTag] = useState<string | null>(null)
  const [showCompleted, setShowCompleted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    send('tasks.list', { include_completed: true })
  }, [send])

  useBridgeEvent('tasks.listResult', useCallback((data: { tasks: Task[] }) => {
    setTasks(data.tasks)
  }, []))

  useBridgeEvent('tasks.created', useCallback((data: { task: Task }) => {
    setTasks(prev => [...prev, data.task])
  }, []))

  useBridgeEvent('tasks.updated', useCallback((data: { task: Task }) => {
    setTasks(prev => prev.map(t => t.id === data.task.id ? data.task : t))
  }, []))

  useBridgeEvent('tasks.completed', useCallback((data: { task: Task }) => {
    setTasks(prev => prev.map(t => t.id === data.task.id ? data.task : t))
  }, []))

  useBridgeEvent('tasks.deleted', useCallback((data: { id: string }) => {
    setTasks(prev => prev.filter(t => t.id !== data.id))
  }, []))

  useBridgeEvent('tasks.error', useCallback((data: { message: string }) => {
    setError(data.message)
    setTimeout(() => setError(null), 5000)
  }, []))

  // Derive tags from tasks
  const allTags = [...new Set(tasks.map(t => t.tag).filter(Boolean))] as string[]

  // Filter
  const filtered = activeTag
    ? tasks.filter(t => t.tag === activeTag)
    : tasks

  const today = new Date().toISOString().split('T')[0]

  // Group tasks
  const overdue = filtered.filter(t => !t.completed && t.due_date && t.due_date < today && !t.parent_id)
  const dueToday = filtered.filter(t => !t.completed && t.due_date === today && !t.parent_id)
  const upcoming = filtered.filter(t => !t.completed && t.due_date && t.due_date > today && !t.parent_id)
  const noDeadline = filtered.filter(t => !t.completed && !t.due_date && !t.parent_id)
  const completed = filtered.filter(t => t.completed && !t.parent_id)

  const subtasksFor = (parentId: string) => tasks.filter(t => t.parent_id === parentId)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col h-full p-4 gap-4"
    >
      <h1 className="text-xl font-heading font-bold text-text">Tasks</h1>

      {error && (
        <div className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</div>
      )}

      <TaskAddInput />

      {allTags.length > 0 && (
        <TagFilter tags={allTags} active={activeTag} onSelect={setActiveTag} />
      )}

      <div className="flex-1 overflow-y-auto space-y-4">
        {overdue.length > 0 && (
          <Section title="Overdue" color="text-destructive">
            {overdue.map(t => (
              <TaskCard key={t.id} task={t} subtasks={subtasksFor(t.id)} />
            ))}
          </Section>
        )}

        {dueToday.length > 0 && (
          <Section title="Today" color="text-primary">
            {dueToday.map(t => (
              <TaskCard key={t.id} task={t} subtasks={subtasksFor(t.id)} />
            ))}
          </Section>
        )}

        {upcoming.length > 0 && (
          <Section title="Upcoming" color="text-text-muted">
            {upcoming.map(t => (
              <TaskCard key={t.id} task={t} subtasks={subtasksFor(t.id)} />
            ))}
          </Section>
        )}

        {noDeadline.length > 0 && (
          <Section title="No deadline" color="text-text-muted">
            {noDeadline.map(t => (
              <TaskCard key={t.id} task={t} subtasks={subtasksFor(t.id)} />
            ))}
          </Section>
        )}

        {completed.length > 0 && (
          <div>
            <button
              onClick={() => setShowCompleted(!showCompleted)}
              className="text-xs text-text-muted hover:text-primary transition-colors cursor-pointer"
            >
              {showCompleted ? 'Hide' : 'Show'} completed ({completed.length})
            </button>
            <AnimatePresence>
              {showCompleted && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-2 space-y-2"
                >
                  {completed.map(t => (
                    <TaskCard key={t.id} task={t} subtasks={subtasksFor(t.id)} />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {tasks.filter(t => !t.parent_id).length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <p className="text-text-muted text-sm">No tasks yet. Add one above!</p>
          </div>
        )}
      </div>
    </motion.div>
  )
}

function Section({ title, color, children }: { title: string; color: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className={`text-xs font-heading font-semibold uppercase tracking-wide mb-2 ${color}`}>
        {title}
      </h3>
      <div className="space-y-2">
        {children}
      </div>
    </div>
  )
}
