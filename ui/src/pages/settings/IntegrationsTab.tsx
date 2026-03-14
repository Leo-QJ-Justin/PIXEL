import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Slider } from '@/components/ui/slider'
import type { Settings } from '@/bridge/types'

interface IntegrationsTabProps {
  settings: Settings
  onChange: (patch: Partial<Settings>) => void
}

function first(val: number | readonly number[]): number {
  return typeof val === 'number' ? val : val[0]
}

export function IntegrationsTab({ settings, onChange }: IntegrationsTabProps) {
  const integrations = settings.integrations ?? {}
  const pomodoro = (integrations.pomodoro ?? {}) as Settings['integrations']['pomodoro']
  const journal = (integrations.journal ?? {}) as Record<string, unknown>
  const weather = (integrations.weather ?? {}) as Record<string, unknown>

  function updateIntegration(name: string, patch: Record<string, unknown>) {
    onChange({
      integrations: {
        ...integrations,
        [name]: { ...(integrations[name] ?? {}), ...patch },
      },
    })
  }

  return (
    <div className="space-y-4">
      {/* Pomodoro */}
      <section className="bg-surface border border-border rounded-default p-4 space-y-3">
        <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide">
          Pomodoro
        </h3>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={pomodoro.enabled ?? true}
            onCheckedChange={(checked: boolean) => updateIntegration('pomodoro', { enabled: checked })}
          />
          <span className="text-sm">Enabled</span>
        </label>
        <div className="space-y-2">
          <Label>Work: {pomodoro.work_duration_minutes ?? 25} min</Label>
          <Slider
            min={5}
            max={60}
            step={5}
            value={[pomodoro.work_duration_minutes ?? 25]}
            onValueChange={(val) => updateIntegration('pomodoro', { work_duration_minutes: first(val) })}
          />
        </div>
        <div className="space-y-2">
          <Label>Short break: {pomodoro.short_break_minutes ?? 5} min</Label>
          <Slider
            min={1}
            max={15}
            step={1}
            value={[pomodoro.short_break_minutes ?? 5]}
            onValueChange={(val) => updateIntegration('pomodoro', { short_break_minutes: first(val) })}
          />
        </div>
        <div className="space-y-2">
          <Label>Long break: {pomodoro.long_break_minutes ?? 15} min</Label>
          <Slider
            min={5}
            max={30}
            step={5}
            value={[pomodoro.long_break_minutes ?? 15]}
            onValueChange={(val) => updateIntegration('pomodoro', { long_break_minutes: first(val) })}
          />
        </div>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={pomodoro.auto_start ?? false}
            onCheckedChange={(checked: boolean) => updateIntegration('pomodoro', { auto_start: checked })}
          />
          <span className="text-sm">Auto-start next session</span>
        </label>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={pomodoro.sound_enabled ?? true}
            onCheckedChange={(checked: boolean) => updateIntegration('pomodoro', { sound_enabled: checked })}
          />
          <span className="text-sm">Sound effects</span>
        </label>
      </section>

      {/* Journal */}
      <section className="bg-surface border border-border rounded-default p-4 space-y-3">
        <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide">
          Journal
        </h3>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={(journal.enabled as boolean) ?? true}
            onCheckedChange={(checked: boolean) => updateIntegration('journal', { enabled: checked })}
          />
          <span className="text-sm">Enabled</span>
        </label>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={(journal.blur_content as boolean) ?? false}
            onCheckedChange={(checked: boolean) => updateIntegration('journal', { blur_content: checked })}
          />
          <span className="text-sm">Blur content in list</span>
        </label>
      </section>

      {/* Weather */}
      <section className="bg-surface border border-border rounded-default p-4 space-y-3">
        <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide">
          Weather
        </h3>
        <div className="space-y-2">
          <Label htmlFor="weather_city">City</Label>
          <Input
            id="weather_city"
            value={(weather.city as string) ?? ''}
            onChange={(e) => updateIntegration('weather', { city: e.target.value })}
            placeholder="e.g. Toronto"
          />
        </div>
      </section>
    </div>
  )
}
