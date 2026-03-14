import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { JournalEntry } from '@/bridge/types'
import { ScrollArea } from '@/components/ui/scroll-area'

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

export function VaultList({ onEntryClick, onNewEntry }: VaultListProps) {
  const { send } = useBridge()
  const [entries, setEntries] = useState<JournalEntry[]>([])

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
      <ScrollArea className="flex-1">
        {entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-text-muted text-sm gap-2">
            <span className="text-3xl">📝</span>
            <p>No journal entries yet.</p>
            <p className="text-xs">Start writing to see them here.</p>
          </div>
        ) : (
          <div className="flex flex-col divide-y divide-border">
            {entries.map((entry, idx) => (
              <motion.button
                key={entry.date}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.04, duration: 0.2 }}
                onClick={() => onEntryClick(entry.date)}
                className="cursor-pointer w-full text-left px-4 py-3 hover:bg-surface-hover transition-colors flex items-start gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-text-muted mb-0.5">{formatDate(entry.date)}</p>
                  <p className="text-sm text-text truncate">
                    {entry.raw_text.slice(0, 80)}
                    {entry.raw_text.length > 80 ? '…' : ''}
                  </p>
                </div>
                {entry.mood && (
                  <span className="text-lg shrink-0 mt-0.5">{moodEmoji(entry.mood)}</span>
                )}
              </motion.button>
            ))}
          </div>
        )}
      </ScrollArea>
    </motion.div>
  )
}
