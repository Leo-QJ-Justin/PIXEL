import { useCallback, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, Play, Pause, SkipForward, Coffee } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import { Button } from '@/components/ui/button'
import { ProgressRing } from './ProgressRing'
import { DiamondStreak } from './DiamondStreak'
import { StatsView } from './StatsView'

type Phase = 'IDLE' | 'FOCUS' | 'SESSION_COMPLETE' | 'SHORT_BREAK' | 'LONG_BREAK'

function formatTime(totalSeconds: number): string {
  const m = Math.floor(Math.abs(totalSeconds) / 60)
  const s = Math.abs(totalSeconds) % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function phaseLabel(phase: Phase, paused: boolean): string {
  if (phase === 'IDLE') return 'Ready to focus?'
  if (phase === 'FOCUS') return paused ? 'PAUSED' : 'FOCUSING...'
  if (phase === 'SESSION_COMPLETE') return 'SESSION CLEAR!'
  if (phase === 'SHORT_BREAK' || phase === 'LONG_BREAK') return paused ? 'PAUSED' : 'RESTING...'
  return ''
}

function phaseColor(phase: Phase): string {
  if (phase === 'FOCUS') return 'var(--color-primary)'
  if (phase === 'SESSION_COMPLETE') return 'var(--color-success)'
  if (phase === 'SHORT_BREAK' || phase === 'LONG_BREAK') return 'var(--color-accent)'
  return 'var(--color-border)'
}

export function PomodoroPage() {
  const { send } = useBridge()

  const [phase, setPhase] = useState<Phase>('IDLE')
  const [remaining, setRemaining] = useState(0)
  const [totalDuration, setTotalDuration] = useState(1500) // 25 min default
  const [completed, setCompleted] = useState(0)
  const [paused, setPaused] = useState(false)

  const [showStats, setShowStats] = useState(false)
  const [stats, setStats] = useState({
    daily: {} as Record<string, number>,
    streak: 0,
    total: 0,
    longest_streak: 0,
  })

  // Timer tick
  useBridgeEvent('timer.tick', useCallback((data: { remaining: number }) => {
    setRemaining(data.remaining)
  }, []))

  // State changes
  useBridgeEvent('timer.state', useCallback((data: { state: string; context: Record<string, unknown> }) => {
    const newPhase = data.state as Phase
    setPhase(newPhase)
    const ctx = data.context
    const rem = (ctx.remaining_seconds as number) ?? 0
    setRemaining(rem)
    setCompleted((ctx.completed_in_cycle as number) ?? 0)
    setPaused((ctx.paused as boolean) ?? false)

    // Update total duration for progress ring
    if (newPhase === 'FOCUS' || newPhase === 'SHORT_BREAK' || newPhase === 'LONG_BREAK') {
      if (rem > 0) setTotalDuration(rem)
    }
  }, []))

  // Session completed
  useBridgeEvent('pomodoro.session', useCallback((data: { completed: number }) => {
    setCompleted(data.completed)
  }, []))

  // Stats updated
  useBridgeEvent('pomodoro.stats', useCallback((data: { daily: Record<string, number>; streak: number; total: number; longest_streak: number }) => {
    setStats(data)
  }, []))

  // Progress: 1 when full, 0 when empty
  const progress = totalDuration > 0 && remaining > 0 ? remaining / totalDuration : phase === 'IDLE' ? 0 : 1

  // Today's count
  const todayStr = new Date().toISOString().split('T')[0]
  const todayCount = stats.daily[todayStr] ?? 0

  if (showStats) {
    return (
      <StatsView
        daily={stats.daily}
        streak={stats.streak}
        total={stats.total}
        longest_streak={stats.longest_streak}
        onBack={() => setShowStats(false)}
      />
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="flex flex-col items-center justify-center min-h-screen bg-background px-4 gap-5"
    >
      {/* Timer ring + countdown */}
      <div className="relative">
        <ProgressRing progress={progress} color={phaseColor(phase)} />
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-heading font-bold text-text tabular-nums">
            {phase === 'IDLE' ? formatTime(totalDuration) : formatTime(remaining)}
          </span>
        </div>
      </div>

      {/* Phase label */}
      <p className="text-sm font-heading font-semibold text-text-muted tracking-wide">
        {phaseLabel(phase, paused)}
      </p>

      {/* Diamond streak (4 diamonds for sessions in cycle) */}
      <DiamondStreak count={4} filled={completed % 4} />

      {/* Action buttons */}
      <div className="flex items-center gap-3">
        {phase === 'IDLE' && (
          <Button
            onClick={() => send('timer.start')}
            className="cursor-pointer gap-1.5"
            size="lg"
          >
            <Play size={16} />
            Start
          </Button>
        )}

        {phase === 'FOCUS' && (
          <>
            <Button
              onClick={() => { send('timer.pause'); setPaused(!paused) }}
              variant="outline"
              className="cursor-pointer gap-1.5"
              size="lg"
            >
              {paused ? <Play size={16} /> : <Pause size={16} />}
              {paused ? 'Resume' : 'Pause'}
            </Button>
            <Button
              onClick={() => send('timer.skip')}
              variant="ghost"
              className="cursor-pointer gap-1.5"
              size="lg"
            >
              <SkipForward size={16} />
              Skip
            </Button>
          </>
        )}

        {phase === 'SESSION_COMPLETE' && (
          <>
            <Button
              onClick={() => send('timer.startBreak')}
              className="cursor-pointer gap-1.5"
              size="lg"
            >
              <Coffee size={16} />
              Start Break
            </Button>
            <Button
              onClick={() => send('timer.skipBreak')}
              variant="ghost"
              className="cursor-pointer gap-1.5"
              size="lg"
            >
              <SkipForward size={16} />
              Skip Break
            </Button>
          </>
        )}

        {(phase === 'SHORT_BREAK' || phase === 'LONG_BREAK') && (
          <>
            <Button
              onClick={() => { send('timer.pause'); setPaused(!paused) }}
              variant="outline"
              className="cursor-pointer gap-1.5"
              size="lg"
            >
              {paused ? <Play size={16} /> : <Pause size={16} />}
              {paused ? 'Resume' : 'Pause'}
            </Button>
            <Button
              onClick={() => send('timer.skip')}
              variant="ghost"
              className="cursor-pointer gap-1.5"
              size="lg"
            >
              <SkipForward size={16} />
              Skip
            </Button>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center gap-3 mt-2">
        <span className="text-xs text-text-muted">
          Today: {todayCount} session{todayCount !== 1 ? 's' : ''}
        </span>
        <button
          onClick={() => setShowStats(true)}
          className="cursor-pointer text-text-muted hover:text-primary transition-colors"
          aria-label="View stats"
        >
          <BarChart3 size={18} />
        </button>
      </div>
    </motion.div>
  )
}
