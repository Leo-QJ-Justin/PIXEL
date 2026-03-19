import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Sparkles, Save } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import type { JournalEntry } from '@/bridge/types'
import { MoodPicker } from './MoodPicker'
import { cn } from '@/lib/utils'

interface EntryEditorProps {
  date?: string
  mode?: string
  prompt?: string
  onSaved: () => void
}

type EditorMode = 'free' | 'guided' | 'mood'

interface ModeOption {
  id: EditorMode
  label: string
  description: string
  emoji: string
}

const MODE_OPTIONS: ModeOption[] = [
  { id: 'free', label: 'Free Write', description: 'Write whatever is on your mind', emoji: '✍️' },
  { id: 'guided', label: 'Guided Reflection', description: 'Answer a daily prompt', emoji: '💭' },
  { id: 'mood', label: 'Quick Mood', description: 'Just log how you feel', emoji: '😊' },
]

const GUIDED_PROMPT = 'What is one thing that challenged you today, and how did you handle it?'

function today(): string {
  return new Date().toISOString().split('T')[0]
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('default', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
}

function modeLabelText(mode: EditorMode): string {
  const found = MODE_OPTIONS.find((m) => m.id === mode)
  return found?.label ?? ''
}

export function EntryEditor({ date, mode: initialMode, prompt: initialPrompt, onSaved }: EntryEditorProps) {
  const { send } = useBridge()

  const targetDate = date ?? today()
  const [selectedMode, setSelectedMode] = useState<EditorMode | null>(
    initialMode ? (initialMode as EditorMode) : null,
  )
  const [mood, setMood] = useState<string | null>(null)
  const [rawText, setRawText] = useState('')
  const [cleanText, setCleanText] = useState('')
  const [showClean, setShowClean] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isCleaning, setIsCleaning] = useState(false)

  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load existing entry if date provided; notify backend of editor lifecycle
  useEffect(() => {
    send('journal.editorOpened')
    if (date) {
      send('journal.loadEntry', { date })
    }
    return () => {
      send('journal.editorClosed')
    }
  }, [send, date])

  useBridgeEvent('journal.entryLoaded', (payload) => {
    if (payload.entry) {
      const e: JournalEntry = payload.entry
      setRawText(e.raw_text)
      setCleanText(e.clean_text)
      setMood(e.mood || null)
      if (!selectedMode && e.mode) {
        setSelectedMode(e.mode as EditorMode)
      }
    }
  })

  useBridgeEvent('journal.cleanedUp', (payload) => {
    setIsCleaning(false)
    if (payload.success && payload.cleanText) {
      setCleanText(payload.cleanText)
      setShowClean(true)
    }
  })

  useBridgeEvent('journal.saved', (payload) => {
    setIsSaving(false)
    if (payload.success) {
      onSaved()
    }
  })

  function buildEntry(): JournalEntry {
    const now = new Date().toISOString()
    return {
      date: targetDate,
      mode: selectedMode ?? 'free',
      mood: mood ?? '',
      raw_text: rawText,
      clean_text: cleanText || rawText,
      prompt_used: selectedMode === 'guided' ? (initialPrompt ?? GUIDED_PROMPT) : '',
      created_at: now,
      updated_at: now,
    }
  }

  function triggerAutosave(text: string) {
    if (autosaveTimer.current) {
      clearTimeout(autosaveTimer.current)
    }
    autosaveTimer.current = setTimeout(() => {
      send('journal.save', {
        entry: {
          ...buildEntry(),
          raw_text: text,
        },
      })
    }, 3000)
  }

  function handleTextChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const text = e.target.value
    setRawText(text)
    setShowClean(false) // revert to raw when editing
    triggerAutosave(text)
  }

  function handleCleanup() {
    setIsCleaning(true)
    send('journal.cleanup', { text: rawText })
  }

  function handleSave() {
    if (autosaveTimer.current) {
      clearTimeout(autosaveTimer.current)
    }
    setIsSaving(true)
    send('journal.save', { entry: buildEntry(), explicit: true })
  }

  // Mode picker screen
  if (!selectedMode) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -16 }}
        transition={{ duration: 0.25 }}
        className="flex flex-col gap-4 p-4"
      >
        <h2 className="font-heading text-xl text-primary">New Entry</h2>
        <p className="text-sm text-text-muted">{formatDateLabel(targetDate)}</p>
        <p className="text-sm text-text">How would you like to write today?</p>

        <div className="flex flex-col gap-3 mt-2">
          {MODE_OPTIONS.map((option) => (
            <button
              key={option.id}
              onClick={() => setSelectedMode(option.id)}
              className={cn(
                'cursor-pointer flex items-center gap-4 p-4 rounded-default border border-border bg-surface',
                'hover:border-primary hover:bg-surface-hover text-left transition-colors',
              )}
            >
              <span className="text-2xl">{option.emoji}</span>
              <div>
                <p className="font-medium text-sm text-text">{option.label}</p>
                <p className="text-xs text-text-muted">{option.description}</p>
              </div>
            </button>
          ))}
        </div>
      </motion.div>
    )
  }

  const activePrompt = selectedMode === 'guided' ? (initialPrompt ?? GUIDED_PROMPT) : null

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col gap-4 p-4 min-h-full"
    >
      {/* Date + mode label */}
      <div>
        <h2 className="font-heading text-xl text-primary">{formatDateLabel(targetDate)}</h2>
        <p className="text-xs text-text-muted mt-0.5">{modeLabelText(selectedMode)}</p>
      </div>

      {/* Prompt card (guided mode) */}
      {activePrompt && (
        <div className="bg-surface border border-border rounded-default p-3">
          <p className="text-xs text-text-muted font-medium mb-1">Today's prompt</p>
          <p className="text-sm text-text leading-snug">{activePrompt}</p>
        </div>
      )}

      {/* Mood picker */}
      <div>
        <p className="text-xs text-text-muted font-medium mb-2">How are you feeling?</p>
        <MoodPicker selected={mood} onChange={setMood} />
      </div>

      {/* Text area (hidden for mood-only) */}
      {selectedMode !== 'mood' && (
        <div className="flex flex-col gap-2 flex-1">
          <textarea
            value={showClean ? cleanText : rawText}
            onChange={handleTextChange}
            readOnly={showClean}
            placeholder="Start writing…"
            className={cn(
              'w-full min-h-[400px] resize-none rounded-default border border-border p-4',
              'text-sm text-text font-serif placeholder:text-text-muted',
              'focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all duration-200',
              showClean && 'opacity-80 cursor-default',
            )}
            style={{
              lineHeight: '28px',
              backgroundColor: '#FFFDF8',
              backgroundImage: 'repeating-linear-gradient(transparent, transparent 27px, #E8D5C0 27px, #E8D5C0 28px)',
              backgroundAttachment: 'local',
              backgroundPosition: '0 15px',
              boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.04)',
            }}
          />

          {/* Toolbar */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleCleanup}
              disabled={isCleaning || !rawText.trim()}
              className={cn(
                'cursor-pointer flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-medium',
                'border border-border bg-surface text-text-muted hover:text-text hover:border-border-hover',
                'transition-colors disabled:opacity-40 disabled:cursor-not-allowed',
              )}
            >
              <Sparkles size={13} />
              {isCleaning ? 'Cleaning…' : 'Clean up'}
            </button>

            {cleanText && (
              <button
                onClick={() => setShowClean((v) => !v)}
                className="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-medium border border-border bg-surface text-text-muted hover:text-text hover:border-border-hover transition-colors"
              >
                {showClean ? <EyeOff size={13} /> : <Eye size={13} />}
                {showClean ? 'Show my words' : 'Show polished'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={isSaving}
        className={cn(
          'cursor-pointer flex items-center justify-center gap-2 w-full py-3 rounded-default',
          'bg-primary text-white font-medium text-sm hover:bg-primary-hover transition-colors',
          'disabled:opacity-60 disabled:cursor-not-allowed',
        )}
      >
        <Save size={15} />
        {isSaving ? 'Saving…' : 'Save & Close'}
      </button>
    </motion.div>
  )
}
