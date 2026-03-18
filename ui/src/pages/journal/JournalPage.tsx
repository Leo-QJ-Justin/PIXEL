import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronLeft } from 'lucide-react'
import { StatsSurface } from './StatsSurface'
import { VaultList } from './VaultList'
import { EntryEditor } from './EntryEditor'

type View = 'stats' | 'vault' | 'editor'

interface EditorCtx {
  date?: string
  mode?: string
  prompt?: string
}

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 40 : -40,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction > 0 ? -40 : 40,
    opacity: 0,
  }),
}

export function JournalPage() {
  const [view, setView] = useState<View>('stats')
  const [editorCtx, setEditorCtx] = useState<EditorCtx>({})
  // direction: 1 = forward (deeper), -1 = back
  const [direction, setDirection] = useState(1)

  function navigate(next: View, ctx?: EditorCtx, dir = 1) {
    setDirection(dir)
    setView(next)
    if (ctx) setEditorCtx(ctx)
  }

  function goBack() {
    if (view === 'editor') {
      navigate(editorCtx.date ? 'vault' : 'stats', {}, -1)
    } else if (view === 'vault') {
      navigate('stats', {}, -1)
    }
  }

  function handleOpenVault() {
    navigate('vault')
  }

  function handleWritePrompt(prompt: string) {
    navigate('editor', { prompt, mode: 'guided' })
  }

  function handleDateClick(date: string) {
    navigate('editor', { date })
  }

  function handleEntryClick(date: string) {
    navigate('editor', { date })
  }

  function handleNewEntry() {
    navigate('editor', {})
  }

  function handleSaved() {
    navigate('vault', {}, -1)
  }

  const showBack = view !== 'stats'

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Back button */}
      <AnimatePresence>
        {showBack && (
          <motion.button
            key="back"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.2 }}
            onClick={goBack}
            className="cursor-pointer absolute top-3 left-3 z-10 flex items-center gap-1 text-sm text-text-muted hover:text-primary transition-colors"
            aria-label="Go back"
          >
            <ChevronLeft size={18} />
            Back
          </motion.button>
        )}
      </AnimatePresence>

      {/* Page content with slide transition */}
      <AnimatePresence mode="wait" custom={direction}>
        {view === 'stats' && (
          <motion.div
            key="stats"
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="flex-1"
          >
            <StatsSurface
              onOpenVault={handleOpenVault}
              onWritePrompt={handleWritePrompt}
              onDateClick={handleDateClick}
            />
          </motion.div>
        )}

        {view === 'vault' && (
          <motion.div
            key="vault"
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="flex-1 pt-10"
          >
            <VaultList
              onEntryClick={handleEntryClick}
              onNewEntry={handleNewEntry}
            />
          </motion.div>
        )}

        {view === 'editor' && (
          <motion.div
            key="editor"
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="flex-1 pt-10"
          >
            <EntryEditor
              date={editorCtx.date}
              mode={editorCtx.mode}
              prompt={editorCtx.prompt}
              onSaved={handleSaved}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
