import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Slider } from '@/components/ui/slider'
import type { Settings } from '@/bridge/types'

interface BehaviorsTabProps {
  settings: Settings
  onChange: (patch: Partial<Settings>) => void
}

function first(val: number | readonly number[]): number {
  return typeof val === 'number' ? val : val[0]
}

export function BehaviorsTab({ settings, onChange }: BehaviorsTabProps) {
  const behaviors = settings.behaviors ?? {}
  const wander = behaviors.wander ?? { wander_chance: 0.3 }
  const wave = behaviors.wave ?? { greeting: 'Hello!' }
  const idle = behaviors.idle_variety ?? { enabled: true, chance: 0.4 }
  const sleep = behaviors.sleep ?? {
    inactivity_timeout_ms: 60000,
    schedule_enabled: false,
    schedule_start: '22:00',
    schedule_end: '06:00',
  }

  function updateBehaviors(patch: Partial<Settings['behaviors']>) {
    onChange({ behaviors: { ...behaviors, ...patch } })
  }

  return (
    <div className="space-y-6">
      {/* Wander */}
      <section className="space-y-3">
        <h3 className="text-sm font-heading font-semibold text-text-muted uppercase tracking-wide">
          Wander
        </h3>
        <div className="space-y-2">
          <Label>Chance: {Math.round((wander.wander_chance ?? 0.3) * 100)}%</Label>
          <Slider
            min={0}
            max={100}
            step={5}
            value={[Math.round((wander.wander_chance ?? 0.3) * 100)]}
            onValueChange={(val) =>
              updateBehaviors({ wander: { ...wander, wander_chance: first(val) / 100 } })
            }
          />
        </div>
      </section>

      {/* Wave */}
      <section className="space-y-3">
        <h3 className="text-sm font-heading font-semibold text-text-muted uppercase tracking-wide">
          Wave
        </h3>
        <div className="space-y-2">
          <Label htmlFor="greeting">Greeting</Label>
          <Input
            id="greeting"
            value={wave.greeting ?? ''}
            onChange={(e) =>
              updateBehaviors({ wave: { ...wave, greeting: e.target.value } })
            }
            placeholder="Hello!"
          />
        </div>
      </section>

      {/* Idle Variety */}
      <section className="space-y-3">
        <h3 className="text-sm font-heading font-semibold text-text-muted uppercase tracking-wide">
          Idle Variety
        </h3>
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={idle.enabled ?? true}
            onCheckedChange={(checked: boolean) =>
              updateBehaviors({ idle_variety: { ...idle, enabled: checked } })
            }
          />
          <span className="text-sm">Enabled</span>
        </label>
        <div className="space-y-2">
          <Label>Chance: {Math.round((idle.chance ?? 0.4) * 100)}%</Label>
          <Slider
            min={0}
            max={100}
            step={5}
            value={[Math.round((idle.chance ?? 0.4) * 100)]}
            onValueChange={(val) =>
              updateBehaviors({ idle_variety: { ...idle, chance: first(val) / 100 } })
            }
          />
        </div>
      </section>

      {/* Sleep */}
      <section className="space-y-3">
        <h3 className="text-sm font-heading font-semibold text-text-muted uppercase tracking-wide">
          Sleep
        </h3>
        <div className="space-y-2">
          <Label>
            Inactivity timeout: {Math.round((sleep.inactivity_timeout_ms ?? 60000) / 1000)}s
          </Label>
          <Slider
            min={10000}
            max={300000}
            step={5000}
            value={[sleep.inactivity_timeout_ms ?? 60000]}
            onValueChange={(val) =>
              updateBehaviors({ sleep: { ...sleep, inactivity_timeout_ms: first(val) } })
            }
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={sleep.schedule_enabled ?? false}
            onCheckedChange={(checked: boolean) =>
              updateBehaviors({ sleep: { ...sleep, schedule_enabled: checked } })
            }
          />
          <span className="text-sm">Sleep schedule</span>
        </label>
        {sleep.schedule_enabled && (
          <div className="flex gap-3 items-center">
            <div className="space-y-1">
              <Label htmlFor="sleep_start">Start</Label>
              <Input
                id="sleep_start"
                type="time"
                value={sleep.schedule_start ?? '22:00'}
                onChange={(e) =>
                  updateBehaviors({ sleep: { ...sleep, schedule_start: e.target.value } })
                }
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="sleep_end">End</Label>
              <Input
                id="sleep_end"
                type="time"
                value={sleep.schedule_end ?? '06:00'}
                onChange={(e) =>
                  updateBehaviors({ sleep: { ...sleep, schedule_end: e.target.value } })
                }
              />
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
