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
  const encouraging = (integrations.encouraging ?? {}) as Settings['integrations']['encouraging']
  const encTriggers = (encouraging.triggers ?? {}) as Settings['integrations']['encouraging']['triggers']

  function updateIntegration(name: string, patch: Record<string, unknown>) {
    onChange({
      integrations: {
        ...integrations,
        [name]: { ...(integrations[name] ?? {}), ...patch },
      },
    })
  }

  function updateEncTrigger(name: string, patch: Record<string, unknown>) {
    updateIntegration('encouraging', {
      triggers: { ...encTriggers, [name]: { ...(encTriggers[name as keyof typeof encTriggers] ?? {}), ...patch } },
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

      {/* Encouraging Messages */}
      <section className="bg-surface border border-border rounded-default p-4 space-y-3">
        <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide">
          Encouraging Messages
        </h3>
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={encouraging.enabled ?? true}
            onCheckedChange={(checked: boolean) => updateIntegration('encouraging', { enabled: checked })}
          />
          <span className="text-sm">Enabled</span>
        </label>
        <div className="space-y-2">
          <Label>Min cooldown: {encouraging.cooldown_min_minutes ?? 30} min</Label>
          <Slider
            min={10}
            max={encouraging.cooldown_max_minutes ?? 60}
            step={5}
            value={[encouraging.cooldown_min_minutes ?? 30]}
            onValueChange={(val) => updateIntegration('encouraging', { cooldown_min_minutes: first(val) })}
          />
        </div>
        <div className="space-y-2">
          <Label>Max cooldown: {encouraging.cooldown_max_minutes ?? 60} min</Label>
          <Slider
            min={encouraging.cooldown_min_minutes ?? 30}
            max={180}
            step={5}
            value={[encouraging.cooldown_max_minutes ?? 60]}
            onValueChange={(val) => updateIntegration('encouraging', { cooldown_max_minutes: first(val) })}
          />
        </div>

        <h4 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide pt-2">
          Triggers
        </h4>

        {/* Restless */}
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={encTriggers.restless?.enabled ?? true}
            onCheckedChange={(checked: boolean) => updateEncTrigger('restless', { enabled: checked })}
          />
          <span className="text-sm">Restless (long sessions)</span>
        </label>
        <div className="space-y-2 pl-7">
          <Label>Threshold: {encTriggers.restless?.threshold_minutes ?? 90} min</Label>
          <Slider
            min={30}
            max={180}
            step={10}
            value={[encTriggers.restless?.threshold_minutes ?? 90]}
            onValueChange={(val) => updateEncTrigger('restless', { threshold_minutes: first(val) })}
          />
        </div>

        {/* Proud */}
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={encTriggers.proud?.enabled ?? true}
            onCheckedChange={(checked: boolean) => updateEncTrigger('proud', { enabled: checked })}
          />
          <span className="text-sm">Proud (habit streaks)</span>
        </label>
        <div className="space-y-2 pl-7">
          <Label>Streak threshold: {encTriggers.proud?.streak_threshold ?? 3} days</Label>
          <Slider
            min={1}
            max={10}
            step={1}
            value={[encTriggers.proud?.streak_threshold ?? 3]}
            onValueChange={(val) => updateEncTrigger('proud', { streak_threshold: first(val) })}
          />
        </div>

        {/* Excited */}
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={encTriggers.excited?.enabled ?? true}
            onCheckedChange={(checked: boolean) => updateEncTrigger('excited', { enabled: checked })}
          />
          <span className="text-sm">Excited (welcome back)</span>
        </label>
        <div className="space-y-2 pl-7">
          <Label>Idle threshold: {encTriggers.excited?.idle_threshold_minutes ?? 15} min</Label>
          <Slider
            min={5}
            max={60}
            step={5}
            value={[encTriggers.excited?.idle_threshold_minutes ?? 15]}
            onValueChange={(val) => updateEncTrigger('excited', { idle_threshold_minutes: first(val) })}
          />
        </div>

        {/* Impressed */}
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={encTriggers.impressed?.enabled ?? true}
            onCheckedChange={(checked: boolean) => updateEncTrigger('impressed', { enabled: checked })}
          />
          <span className="text-sm">Impressed (milestones)</span>
        </label>
        <div className="space-y-2 pl-7">
          <Label>Milestone every: {encTriggers.impressed?.milestone_interval ?? 10} completions</Label>
          <Slider
            min={5}
            max={50}
            step={5}
            value={[encTriggers.impressed?.milestone_interval ?? 10]}
            onValueChange={(val) => updateEncTrigger('impressed', { milestone_interval: first(val) })}
          />
        </div>

        {/* Observant */}
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={encTriggers.observant?.enabled ?? true}
            onCheckedChange={(checked: boolean) => updateEncTrigger('observant', { enabled: checked })}
          />
          <span className="text-sm">Observant (noticing your work)</span>
        </label>

        {/* Curious */}
        <label className="flex items-center gap-2.5 cursor-pointer py-0.5">
          <Checkbox
            checked={encTriggers.curious?.enabled ?? true}
            onCheckedChange={(checked: boolean) => updateEncTrigger('curious', { enabled: checked })}
          />
          <span className="text-sm">Curious (fun facts)</span>
        </label>
      </section>
    </div>
  )
}
