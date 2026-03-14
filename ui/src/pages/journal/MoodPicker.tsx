import { cn } from '@/lib/utils'

interface MoodPickerProps {
  selected: string | null
  onChange: (mood: string) => void
}

const MOODS = ['😊', '🙂', '😐', '😔', '😢']

export function MoodPicker({ selected, onChange }: MoodPickerProps) {
  return (
    <div className="flex items-center gap-2">
      {MOODS.map((mood) => (
        <button
          key={mood}
          onClick={() => onChange(mood)}
          className={cn(
            'cursor-pointer w-10 h-10 rounded-full flex items-center justify-center text-xl transition-all',
            selected === mood
              ? 'bg-primary/20 ring-2 ring-primary scale-110'
              : 'hover:bg-surface',
          )}
          aria-label={mood}
          type="button"
        >
          {mood}
        </button>
      ))}
    </div>
  )
}
