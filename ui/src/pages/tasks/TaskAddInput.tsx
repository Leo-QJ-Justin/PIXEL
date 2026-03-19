import { useCallback, useState } from 'react'
import { Plus } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import { Input } from '@/components/ui/input'

export function TaskAddInput() {
  const { send } = useBridge()
  const [title, setTitle] = useState('')

  useBridgeEvent('tasks.created', useCallback(() => {
    setTitle('')
  }, []))

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) return
    send('tasks.create', { title: trimmed })
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <div className="relative flex-1">
        <Plus size={16} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
        <Input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Add a task..."
          className="pl-8"
        />
      </div>
    </form>
  )
}
