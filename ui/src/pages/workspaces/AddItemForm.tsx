import { useState } from 'react'
import { useBridge } from '@/bridge/context'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface AddItemFormProps {
  workspaceId: string
  onClose: () => void
}

export function AddItemForm({ workspaceId, onClose }: AddItemFormProps) {
  const { send } = useBridge()
  const [type, setType] = useState<'app' | 'url' | 'folder'>('app')
  const [path, setPath] = useState('')
  const [displayName, setDisplayName] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!path.trim()) return
    const name = displayName.trim() || path.split(/[/\\]/).pop() || path
    send('workspaces.addItem', {
      workspace_id: workspaceId,
      type,
      path: path.trim(),
      display_name: name,
    })
  }

  function handleBrowse() {
    if (type === 'folder') {
      send('workspaces.browseFolder')
    } else if (type === 'app') {
      send('workspaces.browseFile')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-surface border border-border rounded-default p-3 space-y-2 w-full max-w-xs">
      <div className="flex gap-1">
        {(['app', 'url', 'folder'] as const).map(t => (
          <button
            key={t}
            type="button"
            onClick={() => setType(t)}
            className={`text-xs px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
              type === t ? 'bg-primary text-white' : 'bg-surface-hover text-text-muted'
            }`}
          >
            {t === 'app' ? 'App' : t === 'url' ? 'URL' : 'Folder'}
          </button>
        ))}
      </div>
      <div className="flex gap-1.5">
        <Input
          value={path}
          onChange={e => setPath(e.target.value)}
          placeholder={type === 'url' ? 'https://...' : 'Path...'}
          className="flex-1"
        />
        {type !== 'url' && (
          <Button type="button" variant="outline" size="sm" onClick={handleBrowse} className="cursor-pointer text-xs">
            Browse
          </Button>
        )}
      </div>
      <Input
        value={displayName}
        onChange={e => setDisplayName(e.target.value)}
        placeholder="Display name (optional)"
      />
      <div className="flex gap-1.5">
        <Button type="submit" size="sm" className="cursor-pointer">Add</Button>
        <Button type="button" variant="ghost" size="sm" onClick={onClose} className="cursor-pointer">Cancel</Button>
      </div>
    </form>
  )
}
