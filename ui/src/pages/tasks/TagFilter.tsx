import { cn } from '@/lib/utils'

interface TagFilterProps {
  tags: string[]
  active: string | null
  onSelect: (tag: string | null) => void
}

export function TagFilter({ tags, active, onSelect }: TagFilterProps) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <button
        onClick={() => onSelect(null)}
        className={cn(
          'text-xs px-2 py-0.5 rounded-full transition-colors cursor-pointer',
          active === null
            ? 'bg-primary text-white'
            : 'bg-surface border border-border text-text-muted hover:border-border-hover',
        )}
      >
        All
      </button>
      {tags.map(tag => (
        <button
          key={tag}
          onClick={() => onSelect(active === tag ? null : tag)}
          className={cn(
            'text-xs px-2 py-0.5 rounded-full transition-colors cursor-pointer',
            active === tag
              ? 'bg-primary text-white'
              : 'bg-surface border border-border text-text-muted hover:border-border-hover',
          )}
        >
          {tag}
        </button>
      ))}
    </div>
  )
}
