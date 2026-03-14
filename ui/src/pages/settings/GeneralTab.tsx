import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Slider } from '@/components/ui/slider'
import type { Settings } from '@/bridge/types'

interface GeneralTabProps {
  settings: Settings
  onChange: (patch: Partial<Settings>) => void
}

export function GeneralTab({ settings, onChange }: GeneralTabProps) {
  const general = settings.general ?? {}
  const bubble = general.speech_bubble ?? { enabled: true, duration_ms: 3000 }

  function updateGeneral(patch: Partial<Settings['general']>) {
    onChange({ general: { ...general, ...patch } })
  }

  return (
    <div className="space-y-4">
      {/* Profile */}
      <section className="bg-surface border border-border rounded-default p-4 space-y-3">
        <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide">
          Profile
        </h3>
        <div className="space-y-2">
          <Label htmlFor="user_name">Name</Label>
          <Input
            id="user_name"
            value={settings.user_name ?? ''}
            onChange={(e) => onChange({ user_name: e.target.value })}
            placeholder="Your name"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="birthday">Birthday</Label>
          <Input
            id="birthday"
            type="date"
            value={settings.birthday ?? ''}
            onChange={(e) => onChange({ birthday: e.target.value })}
          />
        </div>
      </section>

      {/* Window */}
      <section className="bg-surface border border-border rounded-default p-4 space-y-3">
        <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide">
          Window
        </h3>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={general.always_on_top ?? true}
            onCheckedChange={(checked: boolean) => updateGeneral({ always_on_top: checked })}
          />
          <span className="text-sm">Always on top</span>
        </label>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={general.start_minimized ?? false}
            onCheckedChange={(checked: boolean) => updateGeneral({ start_minimized: checked })}
          />
          <span className="text-sm">Start minimized</span>
        </label>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={general.start_on_boot ?? false}
            onCheckedChange={(checked: boolean) => updateGeneral({ start_on_boot: checked })}
          />
          <span className="text-sm">Start on boot</span>
        </label>
        <div className="space-y-2">
          <Label htmlFor="facing">Default facing</Label>
          <select
            id="facing"
            value={general.sprite_default_facing ?? 'right'}
            onChange={(e) => updateGeneral({ sprite_default_facing: e.target.value })}
            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm cursor-pointer focus:border-ring focus:ring-3 focus:ring-ring/50 outline-none transition-colors"
          >
            <option value="right">Right</option>
            <option value="left">Left</option>
          </select>
        </div>
      </section>

      {/* Speech Bubble */}
      <section className="bg-surface border border-border rounded-default p-4 space-y-3">
        <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide">
          Speech Bubble
        </h3>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={bubble.enabled}
            onCheckedChange={(checked: boolean) =>
              updateGeneral({ speech_bubble: { ...bubble, enabled: checked } })
            }
          />
          <span className="text-sm">Enabled</span>
        </label>
        <div className="space-y-2">
          <Label>Duration: {((bubble.duration_ms ?? 3000) / 1000).toFixed(1)}s</Label>
          <Slider
            min={1000}
            max={10000}
            step={500}
            value={[bubble.duration_ms ?? 3000]}
            onValueChange={(val) => {
              const v = typeof val === 'number' ? val : val[0]
              updateGeneral({ speech_bubble: { ...bubble, duration_ms: v } })
            }}
          />
        </div>
      </section>
    </div>
  )
}
