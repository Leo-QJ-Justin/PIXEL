import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, Trash2 } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { JournalEntry } from '@/bridge/types'
import { cn } from '@/lib/utils'

interface VaultListProps {
  onEntryClick: (date: string) => void
  onNewEntry: () => void
}

const EMOJI_MAP: Record<string, string> = {
  happy: '😊',
  good: '🙂',
  neutral: '😐',
  sad: '😔',
  bad: '😢',
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('default', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
}

function moodEmoji(mood: string): string {
  return EMOJI_MAP[mood] ?? mood
}

const MODE_LABELS: Record<string, string> = {
  free: 'Free Write',
  guided: 'Guided',
  mood: 'Quick Mood',
}

function modeLabel(mode: string): string {
  return MODE_LABELS[mode] ?? mode.charAt(0).toUpperCase() + mode.slice(1)
}

export function VaultList({ onEntryClick, onNewEntry }: VaultListProps) {
  const { send } = useBridge()
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [revealedDates, setRevealedDates] = useState<Set<string>>(new Set())

  function handleCardClick(date: string) {
    if (revealedDates.has(date)) {
      onEntryClick(date)
    } else {
      setRevealedDates((prev) => new Set(prev).add(date))
    }
  }

  function handleCardKeyDown(e: React.KeyboardEvent, date: string) {
    if (e.target !== e.currentTarget) return
    if (e.key === 'Enter') {
      onEntryClick(date)
    } else if (e.key === ' ') {
      e.preventDefault()
      setRevealedDates((prev) => {
        const next = new Set(prev)
        if (next.has(date)) {
          next.delete(date)
        } else {
          next.add(date)
        }
        return next
      })
    }
  }

  function handleDelete(e: React.MouseEvent, date: string) {
    e.stopPropagation()
    if (window.confirm('Delete this journal entry? This cannot be undone.')) {
      send('journal.delete', { date })
      setEntries((prev) => prev.filter((entry) => entry.date !== date))
      setRevealedDates((prev) => {
        const next = new Set(prev)
        next.delete(date)
        return next
      })
    }
  }

  useEffect(() => {
    send('journal.loadEntries', {})
  }, [send])

  useBridgeEvent('journal.entriesLoaded', (payload) => {
    setEntries(payload.entries)
  })

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h2 className="font-heading text-lg text-primary">Journal Entries</h2>
        <button
          onClick={onNewEntry}
          className="cursor-pointer flex items-center gap-1 text-xs text-primary font-medium hover:bg-surface px-2 py-1 rounded-sm transition-colors"
        >
          <Plus size={14} />
          New Entry
        </button>
      </div>

      {/* Entry list */}
      <div className="flex-1 overflow-y-auto">
        {entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-text-muted text-sm gap-2">
            <span className="text-3xl">📝</span>
            <p>No journal entries yet.</p>
            <p className="text-xs">Start writing to see them here.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3 p-4">
            {entries.map((entry, idx) => {
              const isRevealed = revealedDates.has(entry.date)
              const previewText = entry.raw_text
                ? entry.raw_text.slice(0, 100) + (entry.raw_text.length > 100 ? '…' : '')
                : 'Mood check-in'

              return (
                <motion.div
                  key={entry.date}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04, duration: 0.2 }}
                  role="button"
                  tabIndex={0}
                  onClick={() => handleCardClick(entry.date)}
                  onKeyDown={(e) => handleCardKeyDown(e, entry.date)}
                  aria-label={`Journal entry from ${formatDate(entry.date)}${entry.mood ? `, mood: ${entry.mood}` : ''}`}
                  className={cn(
                    'group cursor-pointer bg-surface border border-border rounded-default shadow-sm p-4',
                    'hover:border-border-hover transition-colors duration-200',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
                  )}
                >
                  {/* Top row: date + mode + mood */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-text-muted">
                      {formatDate(entry.date)}
                    </span>
                    {entry.mode && (
                      <span className="text-xs text-primary bg-surface-hover px-1.5 py-0.5 rounded">
                        {modeLabel(entry.mode)}
                      </span>
                    )}
                    <span className="flex items-center gap-2 ml-auto shrink-0">
                      {entry.mood && (
                        <span className="text-base">
                          {moodEmoji(entry.mood)}
                        </span>
                      )}
                      <button
                        onClick={(e) => handleDelete(e, entry.date)}
                        aria-label={`Delete entry from ${formatDate(entry.date)}`}
                        className="cursor-pointer p-1 rounded text-text-muted opacity-0 group-hover:opacity-100 hover:text-destructive hover:bg-destructive/10 transition-all duration-200 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                      >
                        <Trash2 size={14} />
                      </button>
                    </span>
                  </div>

                  {/* Blurred preview */}
                  <p
                    className={cn(
                      'text-sm text-text line-clamp-2 select-none',
                      'transition-[filter] duration-300 ease-out',
                      !isRevealed && 'blur-[4px]',
                    )}
                  >
                    {previewText}
                  </p>

                  {/* Reveal hint */}
                  {!isRevealed && (
                    <p className="text-xs text-text-muted mt-1.5 text-right">
                      Click to reveal
                    </p>
                  )}
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </motion.div>
  )
}
