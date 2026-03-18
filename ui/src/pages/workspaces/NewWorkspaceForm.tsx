import { useState } from 'react'
import { useBridge } from '@/bridge/context'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const EMOJI_OPTIONS = ['💻', '🎨', '📚', '💬', '🔬', '📊', '🎮', '🏠', '✏️', '🎵', '📁', '🚀']
const COLOR_OPTIONS = ['#3B7DD8', '#E8720C', '#2D9F5B', '#D63B3B', '#9333EA', '#0891B2', '#CA8A04', '#64748B']

interface NewWorkspaceFormProps {
  onClose: () => void
}

export function NewWorkspaceForm({ onClose }: NewWorkspaceFormProps) {
  const { send } = useBridge()
  const [name, setName] = useState('')
  const [icon, setIcon] = useState('💻')
  const [color, setColor] = useState('#3B7DD8')
  const [description, setDescription] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    send('workspaces.create', {
      name: name.trim(),
      icon,
      color,
      description: description.trim() || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-surface border border-border rounded-default p-4 space-y-3">
      <Input
        value={name}
        onChange={e => setName(e.target.value)}
        placeholder="Workspace name..."
        autoFocus
      />

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

      <div>
        <p className="text-xs text-text-muted mb-1.5">Color</p>
        <div className="flex gap-1.5">
          {COLOR_OPTIONS.map(c => (
            <button
              key={c}
              type="button"
              onClick={() => setColor(c)}
              className={`w-6 h-6 rounded-full cursor-pointer transition-transform ${
                color === c ? 'ring-2 ring-offset-2 ring-primary scale-110' : ''
              }`}
              style={{ backgroundColor: c }}
            />
          ))}
        </div>
      </div>

      <Input
        value={description}
        onChange={e => setDescription(e.target.value)}
        placeholder="Description (optional)"
      />

      <div className="flex gap-2">
        <Button type="submit" size="sm" className="cursor-pointer">Create</Button>
        <Button type="button" variant="ghost" size="sm" onClick={onClose} className="cursor-pointer">Cancel</Button>
      </div>
    </form>
  )
}
