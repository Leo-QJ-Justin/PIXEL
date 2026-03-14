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
    <div className="space-y-6">
      {/* Profile */}
      <section className="space-y-3">
        <h3 className="text-sm font-heading font-semibold text-text-muted uppercase tracking-wide">
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
      <section className="space-y-3">
        <h3 className="text-sm font-heading font-semibold text-text-muted uppercase tracking-wide">
          Window
        </h3>
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={general.always_on_top ?? true}
            onCheckedChange={(checked: boolean) => updateGeneral({ always_on_top: checked })}
          />
          <span className="text-sm">Always on top</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={general.start_minimized ?? false}
            onCheckedChange={(checked: boolean) => updateGeneral({ start_minimized: checked })}
          />
          <span className="text-sm">Start minimized</span>
        </label>
      </section>

      {/* Speech Bubble */}
      <section className="space-y-3">
        <h3 className="text-sm font-heading font-semibold text-text-muted uppercase tracking-wide">
          Speech Bubble
        </h3>
        <label className="flex items-center gap-2 cursor-pointer">
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
