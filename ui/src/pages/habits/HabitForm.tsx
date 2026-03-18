import { useState } from 'react'
import { motion } from 'framer-motion'
import { X } from 'lucide-react'
import { useBridge } from '@/bridge/context'

const EMOJI_OPTIONS = [
  '\uD83D\uDCA7', '\uD83C\uDFCB\uFE0F', '\uD83D\uDCD6', '\uD83E\uDDD8', '\uD83D\uDC8A', '\uD83C\uDF3F', '\uD83C\uDFAF', '\uD83D\uDCDD',
  '\uD83C\uDFC3', '\u270D\uFE0F', '\uD83C\uDF4E', '\uD83D\uDE34', '\uD83E\uDDF9', '\uD83D\uDCBB', '\uD83C\uDFA8', '\uD83C\uDFB5',
  '\uD83C\uDF05', '\uD83D\uDCDA', '\uD83D\uDD2C', '\u2705',
]

type Frequency = 'daily' | 'weekly' | 'x_per_week'

interface HabitFormProps {
  onClose: () => void
}

export function HabitForm({ onClose }: HabitFormProps) {
  const { send } = useBridge()
  const [title, setTitle] = useState('')
  const [icon, setIcon] = useState('\u2705')
  const [frequency, setFrequency] = useState<Frequency>('daily')
  const [targetCount, setTargetCount] = useState(3)
  const [reminderTime, setReminderTime] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return

    send('habits.create', {
      title: title.trim(),
      icon,
      frequency,
      target_count: frequency === 'x_per_week' ? targetCount : 1,
      reminder_time: reminderTime || undefined,
    })
  }

  return (
    <motion.form
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2 }}
      onSubmit={handleSubmit}
      className="rounded-lg border border-border bg-surface p-4 flex flex-col gap-3"
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-text">New Habit</span>
        <button
          type="button"
          onClick={onClose}
          className="cursor-pointer text-text-muted hover:text-text"
        >
          <X size={16} />
        </button>
      </div>

      {/* Title */}
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Habit name..."
        autoFocus
        className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/50"
      />

      {/* Icon picker */}
      <div>
        <label className="text-xs text-text-muted mb-1 block">Icon</label>
        <div className="flex flex-wrap gap-1.5">
          {EMOJI_OPTIONS.map((emoji) => (
            <button
              key={emoji}
              type="button"
              onClick={() => setIcon(emoji)}
              className={`cursor-pointer w-8 h-8 rounded-md flex items-center justify-center text-base transition-colors ${
                icon === emoji
                  ? 'bg-primary/20 ring-2 ring-primary'
                  : 'hover:bg-surface-elevated'
              }`}
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Frequency */}
      <div>
        <label className="text-xs text-text-muted mb-1 block">Frequency</label>
        <div className="flex gap-1.5">
          {(['daily', 'weekly', 'x_per_week'] as Frequency[]).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFrequency(f)}
              className={`cursor-pointer flex-1 py-1.5 rounded-md text-xs font-medium transition-colors ${
                frequency === f
                  ? 'bg-primary text-white'
                  : 'bg-surface-elevated text-text-muted hover:text-text'
              }`}
            >
              {f === 'daily' ? 'Daily' : f === 'weekly' ? 'Weekly' : 'X/Week'}
            </button>
          ))}
        </div>
      </div>

      {/* Target count (x_per_week) */}
      {frequency === 'x_per_week' && (
        <div>
          <label className="text-xs text-text-muted mb-1 block">
            Times per week: {targetCount}
          </label>
          <input
            type="range"
            min={1}
            max={7}
            value={targetCount}
            onChange={(e) => setTargetCount(Number(e.target.value))}
            className="w-full"
          />
        </div>
      )}

      {/* Reminder time */}
      <div>
        <label className="text-xs text-text-muted mb-1 block">
          Reminder time (optional)
        </label>
        <input
          type="time"
          value={reminderTime}
          onChange={(e) => setReminderTime(e.target.value)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={!title.trim()}
        className="cursor-pointer w-full py-2 rounded-md bg-primary text-white text-sm font-medium disabled:opacity-50 hover:bg-primary/90 transition-colors"
      >
        Add Habit
      </button>
    </motion.form>
  )
}
