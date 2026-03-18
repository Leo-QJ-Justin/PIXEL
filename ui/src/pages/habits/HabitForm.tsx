import { useState } from 'react'
import { useBridge } from '@/bridge/context'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const EMOJI_OPTIONS = ['💧', '🏋️', '📖', '🧘', '💊', '🌿', '🎯', '📝', '🏃', '✍️', '🍎', '😴', '🧹', '💻', '🎨', '🎵', '🌅', '📚', '🔬', '✅']

interface HabitFormProps {
  onClose: () => void
}

export function HabitForm({ onClose }: HabitFormProps) {
  const { send } = useBridge()
  const [title, setTitle] = useState('')
  const [icon, setIcon] = useState('✅')
  const [frequency, setFrequency] = useState<'daily' | 'weekly' | 'x_per_week'>('daily')
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
    <form onSubmit={handleSubmit} className="bg-surface border border-border rounded-default p-4 space-y-3">
      <Input
        value={title}
        onChange={e => setTitle(e.target.value)}
        placeholder="Habit name..."
        autoFocus
      />

      {/* Emoji picker */}
      <div>
        <p className="text-xs text-text-muted mb-1.5">Icon</p>
        <div className="flex flex-wrap gap-1">
          {EMOJI_OPTIONS.map(emoji => (
            <button
              key={emoji}
              type="button"
              onClick={() => setIcon(emoji)}
              className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg cursor-pointer transition-colors ${
                icon === emoji ? 'bg-primary/10 ring-2 ring-primary' : 'hover:bg-surface-hover'
              }`}
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Frequency */}
      <div>
        <p className="text-xs text-text-muted mb-1.5">Frequency</p>
        <div className="flex gap-1.5">
          {(['daily', 'weekly', 'x_per_week'] as const).map(f => (
            <button
              key={f}
              type="button"
              onClick={() => setFrequency(f)}
              className={`text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                frequency === f ? 'bg-primary text-white' : 'bg-surface-hover text-text-muted'
              }`}
            >
              {f === 'daily' ? 'Daily' : f === 'weekly' ? 'Weekly' : 'X/Week'}
            </button>
          ))}
        </div>
        {frequency === 'x_per_week' && (
          <div className="flex items-center gap-2 mt-2">
            <Input
              type="number"
              min={1}
              max={7}
              value={targetCount}
              onChange={e => setTargetCount(Number(e.target.value))}
              className="w-16"
            />
            <span className="text-xs text-text-muted">times per week</span>
          </div>
        )}
      </div>

      {/* Reminder time */}
      <div>
        <p className="text-xs text-text-muted mb-1.5">Reminder time (optional)</p>
        <Input
          type="time"
          value={reminderTime}
          onChange={e => setReminderTime(e.target.value)}
          className="w-32"
        />
      </div>

      <div className="flex gap-2">
        <Button type="submit" size="sm" className="cursor-pointer">Save</Button>
        <Button type="button" variant="ghost" size="sm" onClick={onClose} className="cursor-pointer">Cancel</Button>
      </div>
    </form>
  )
}
