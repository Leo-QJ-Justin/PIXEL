import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, Play, Trash2, Rocket } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import { Button } from '@/components/ui/button'
import { WorkspaceItemCard } from './WorkspaceItemCard'
import { AddItemForm } from './AddItemForm'
import { NewWorkspaceForm } from './NewWorkspaceForm'

interface WorkspaceItem {
  id: string
  type: 'app' | 'url' | 'folder'
  path: string
  display_name: string
}

interface Workspace {
  id: string
  name: string
  description: string
  icon: string
  color: string
  behavior: string | null
  items: WorkspaceItem[]
  last_launched: string | null
}

export function WorkspacesPage() {
  const { send } = useBridge()
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [showAddItem, setShowAddItem] = useState(false)
  const [showNewWs, setShowNewWs] = useState(false)

  useEffect(() => {
    send('workspaces.list')
  }, [send])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useBridgeEvent('workspaces.listResult', useCallback((data: any) => {
    const wsList = data.workspaces as Workspace[]
    setWorkspaces(wsList)
    if (wsList.length > 0 && !activeId) {
      setActiveId(wsList[0].id)
    }
  }, [activeId]))

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useBridgeEvent('workspaces.created', useCallback((data: any) => {
    const ws = data.workspace as Workspace
    setWorkspaces(prev => [...prev, ws])
    setActiveId(ws.id)
    setShowNewWs(false)
  }, []))

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useBridgeEvent('workspaces.updated', useCallback((data: any) => {
    const ws = data.workspace as Workspace
    setWorkspaces(prev => prev.map(w => w.id === ws.id ? ws : w))
  }, []))

  useBridgeEvent('workspaces.deleted', useCallback((data: { id: string }) => {
    setWorkspaces(prev => {
      const next = prev.filter(w => w.id !== data.id)
      if (activeId === data.id) setActiveId(next[0]?.id || null)
      return next
    })
  }, [activeId]))

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useBridgeEvent('workspaces.itemAdded', useCallback((data: any) => {
    const ws = data.workspace as Workspace
    setWorkspaces(prev => prev.map(w => w.id === ws.id ? ws : w))
    setShowAddItem(false)
  }, []))

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useBridgeEvent('workspaces.itemRemoved', useCallback((data: any) => {
    const ws = data.workspace as Workspace
    setWorkspaces(prev => prev.map(w => w.id === ws.id ? ws : w))
  }, []))

  const active = workspaces.find(w => w.id === activeId)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col h-full p-4 gap-4"
    >
      <h1 className="text-xl font-heading font-bold text-text">Workspaces</h1>

      {/* Workspace tabs */}
      <div className="flex items-center gap-2 flex-wrap">
        {workspaces.map(ws => (
          <button
            key={ws.id}
            onClick={() => setActiveId(ws.id)}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 ${
              ws.id === activeId
                ? 'text-white'
                : 'bg-surface border border-border text-text-muted hover:border-border-hover'
            }`}
            style={ws.id === activeId ? { backgroundColor: ws.color } : undefined}
          >
            <span>{ws.icon}</span>
            <span>{ws.name}</span>
            <span className="text-[10px] opacity-70">{ws.items.length}</span>
          </button>
        ))}
        <button
          onClick={() => setShowNewWs(true)}
          className="text-xs px-3 py-1.5 rounded-lg border border-dashed border-border text-text-muted hover:border-primary hover:text-primary transition-colors cursor-pointer flex items-center gap-1"
        >
          <Plus size={14} />
          New Workspace
        </button>
      </div>

      {showNewWs && <NewWorkspaceForm onClose={() => setShowNewWs(false)} />}

      {/* Active workspace detail */}
      {active ? (
        <div className="flex-1 overflow-y-auto space-y-4">
          <div className="bg-surface border border-border rounded-default p-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-heading font-bold text-text">{active.name}</h2>
                {active.description && (
                  <p className="text-xs text-text-muted mt-0.5">{active.description}</p>
                )}
                {active.last_launched && (
                  <p className="text-[10px] text-text-muted mt-1">
                    Last used {new Date(active.last_launched).toLocaleDateString()}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => send('workspaces.delete', { id: active.id })}
                  className="text-text-muted hover:text-destructive transition-colors cursor-pointer"
                >
                  <Trash2 size={16} />
                </button>
                <Button
                  onClick={() => send('workspaces.launch', { id: active.id })}
                  className="cursor-pointer gap-1.5"
                >
                  <Play size={14} />
                  Launch
                </Button>
              </div>
            </div>
          </div>

          {/* Items grid */}
          <div className="flex flex-wrap gap-2">
            {active.items.map(item => (
              <WorkspaceItemCard
                key={item.id}
                item={item}
                workspaceId={active.id}
              />
            ))}
            {showAddItem ? (
              <AddItemForm workspaceId={active.id} onClose={() => setShowAddItem(false)} />
            ) : (
              <button
                onClick={() => setShowAddItem(true)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-dashed border-border text-xs text-text-muted hover:border-primary hover:text-primary transition-colors cursor-pointer"
              >
                <Plus size={14} />
                Add Item
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <Rocket size={40} className="text-text-muted mb-3" />
          <p className="text-sm text-text-muted">No workspaces yet. Create one to launch your apps, URLs, and folders with a single click.</p>
        </div>
      )}
    </motion.div>
  )
}
