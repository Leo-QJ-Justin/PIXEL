import { Monitor, Globe, Folder, X } from 'lucide-react'
import { useBridge } from '@/bridge/context'

const TYPE_CONFIG = {
  app: { icon: Monitor, badge: 'APP', badgeClass: 'bg-accent/10 text-accent' },
  url: { icon: Globe, badge: 'URL', badgeClass: 'bg-success/10 text-success' },
  folder: { icon: Folder, badge: 'FOLDER', badgeClass: 'bg-primary/10 text-primary' },
}

interface WorkspaceItemCardProps {
  item: {
    id: string
    type: 'app' | 'url' | 'folder'
    path: string
    display_name: string
  }
  workspaceId: string
}

export function WorkspaceItemCard({ item, workspaceId }: WorkspaceItemCardProps) {
  const { send } = useBridge()
  const config = TYPE_CONFIG[item.type] || TYPE_CONFIG.app
  const Icon = config.icon

  return (
    <div className="group relative flex items-center gap-2 px-3 py-2 rounded-lg bg-surface border border-border">
      <Icon size={16} className="text-text-muted shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-text truncate max-w-[100px]">{item.display_name}</p>
      </div>
      <span className={`text-[9px] font-semibold uppercase px-1 py-0.5 rounded ${config.badgeClass}`}>
        {config.badge}
      </span>
      <button
        onClick={() => send('workspaces.removeItem', { workspace_id: workspaceId, item_id: item.id })}
        className="opacity-0 group-hover:opacity-100 transition-opacity text-text-muted hover:text-destructive cursor-pointer absolute -top-1 -right-1 bg-surface border border-border rounded-full w-4 h-4 flex items-center justify-center"
      >
        <X size={10} />
      </button>
    </div>
  )
}
