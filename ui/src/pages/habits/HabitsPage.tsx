import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { HabitWithStatus } from '@/bridge/types'
import { HabitRow } from './HabitRow'
import { HabitForm } from './HabitForm'
import { WeekGrid } from './WeekGrid'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function HabitsPage() {
  const { send } = useBridge()
  const [habits, setHabits] = useState<HabitWithStatus[]>([])
  const [view, setView] = useState<'today' | 'stats'>('today')
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    send('habits.today')
  }, [send])

  useBridgeEvent('habits.todayResult', useCallback((data: { habits: HabitWithStatus[] }) => {
    setHabits(data.habits)
  }, []))

  useBridgeEvent('habits.completed', useCallback((data: { habit: HabitWithStatus }) => {
    if (data.habit) {
      setHabits(prev => prev.map(h => h.id === data.habit.id ? data.habit : h))
    }
  }, []))

  useBridgeEvent('habits.uncompleted', useCallback((data: { habit: HabitWithStatus }) => {
    if (data.habit) {
      setHabits(prev => prev.map(h => h.id === data.habit.id ? data.habit : h))
    }
  }, []))

  useBridgeEvent('habits.created', useCallback(() => {
    send('habits.today')
    setShowForm(false)
  }, [send]))

  useBridgeEvent('habits.deleted', useCallback((data: { id: string }) => {
    setHabits(prev => prev.filter(h => h.id !== data.id))
  }, []))

  useBridgeEvent('habits.error', useCallback((data: { message: string }) => {
    setError(data.message)
    setTimeout(() => setError(null), 5000)
  }, []))

  const incomplete = habits.filter(h => !h.completed_today)
  const completed = habits.filter(h => h.completed_today)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col h-full p-4 gap-4"
    >
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-heading font-bold text-text">Habits</h1>
        <div className="flex bg-surface border border-border rounded-lg overflow-hidden">
          <button
            onClick={() => setView('today')}
            className={`text-xs px-3 py-1.5 transition-colors cursor-pointer ${
              view === 'today' ? 'bg-primary text-white' : 'text-text-muted hover:text-text'
            }`}
          >
            Today
          </button>
          <button
            onClick={() => setView('stats')}
            className={`text-xs px-3 py-1.5 transition-colors cursor-pointer ${
              view === 'stats' ? 'bg-primary text-white' : 'text-text-muted hover:text-text'
            }`}
          >
            Stats
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</div>
      )}

      {view === 'today' ? (
        <div className="flex-1 overflow-y-auto space-y-2">
          {incomplete.map(h => (
            <HabitRow key={h.id} habit={h} />
          ))}
          {completed.map(h => (
            <HabitRow key={h.id} habit={h} />
          ))}

          {habits.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-text-muted text-sm mb-3">No habits yet. Start building consistency!</p>
            </div>
          )}

          {showForm ? (
            <HabitForm onClose={() => setShowForm(false)} />
          ) : (
            <Button
              onClick={() => setShowForm(true)}
              variant="ghost"
              className="w-full cursor-pointer gap-1.5 text-text-muted"
            >
              <Plus size={16} />
              Add habit
            </Button>
          )}
        </div>
      ) : (
        <WeekGrid habits={habits} />
      )}
    </motion.div>
  )
}
