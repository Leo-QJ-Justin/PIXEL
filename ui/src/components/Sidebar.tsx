import { useLocation, useNavigate } from 'react-router-dom'
import { useBridge } from '@/bridge/context'
import {
  Home,
  ListTodo,
  BookOpen,
  Timer,
  CheckCircle,
  BarChart3,
  Rocket,
  Settings,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  path: string
  label: string
  icon: React.ComponentType<{ size?: number; className?: string }>
}

const mainNav: NavItem[] = [
  { path: '/home', label: 'Home', icon: Home },
  { path: '/tasks', label: 'Tasks', icon: ListTodo },
  { path: '/journal', label: 'Journal', icon: BookOpen },
  { path: '/pomodoro', label: 'Focus', icon: Timer },
  { path: '/habits', label: 'Habits', icon: CheckCircle },
  { path: '/screen-time', label: 'Screen Time', icon: BarChart3 },
  { path: '/workspaces', label: 'Spaces', icon: Rocket },
]

const settingsNav: NavItem = {
  path: '/settings',
  label: 'Settings',
  icon: Settings,
}

interface SidebarProps {
  collapsed: boolean
}

export function Sidebar({ collapsed }: SidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { send } = useBridge()

  const isActive = (path: string) => location.pathname === path

  const handleNav = (path: string) => {
    navigate(path)
    send('window.navigate', { route: path })
  }

  return (
    <nav
      className={cn(
        'flex flex-col shrink-0 border-r border-border py-2 transition-[width] duration-200 ease-in-out',
        collapsed ? 'w-[52px]' : 'w-[140px]',
      )}
      style={{
        background:
          'linear-gradient(180deg, var(--color-surface-hover), var(--color-background))',
      }}
    >
      <div className="flex flex-col gap-0.5 px-2">
        {mainNav.map((item) => (
          <SidebarItem
            key={item.path}
            item={item}
            active={isActive(item.path)}
            collapsed={collapsed}
            onClick={() => handleNav(item.path)}
          />
        ))}
      </div>

      <div className="flex-1" />

      <div className="border-t border-border mt-2 pt-2 px-2">
        <SidebarItem
          item={settingsNav}
          active={isActive(settingsNav.path)}
          collapsed={collapsed}
          onClick={() => handleNav(settingsNav.path)}
        />
      </div>
    </nav>
  )
}

interface SidebarItemProps {
  item: NavItem
  active: boolean
  collapsed: boolean
  onClick: () => void
}

function SidebarItem({ item, active, collapsed, onClick }: SidebarItemProps) {
  const Icon = item.icon

  return (
    <button
      onClick={onClick}
      title={collapsed ? item.label : undefined}
      className={cn(
        'flex items-center gap-2 rounded-lg transition-colors w-full text-left',
        collapsed ? 'justify-center px-0 py-2' : 'px-2.5 py-2',
        active
          ? 'bg-primary text-white'
          : 'text-text hover:bg-surface-hover',
      )}
    >
      <Icon size={18} className="shrink-0" />
      {!collapsed && (
        <span className="text-[13px] font-medium truncate">{item.label}</span>
      )}
    </button>
  )
}
