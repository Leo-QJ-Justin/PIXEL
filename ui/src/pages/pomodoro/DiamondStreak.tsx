interface DiamondStreakProps {
  count: number
  filled: number
}

export function DiamondStreak({ count, filled }: DiamondStreakProps) {
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: count }, (_, i) => (
        <div
          key={i}
          className={`w-3 h-3 rotate-45 rounded-[2px] transition-colors ${
            i < filled ? 'bg-amber-400' : 'bg-border'
          }`}
        />
      ))}
    </div>
  )
}
