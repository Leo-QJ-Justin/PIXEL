import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import type { Settings } from '@/bridge/types'

interface PersonalityTabProps {
  settings: Settings
  onChange: (patch: Partial<Settings>) => void
}

export function PersonalityTab({ settings, onChange }: PersonalityTabProps) {
  const pe = settings.personality_engine ?? {
    enabled: false,
    provider: 'openai',
    model: 'gpt-4o-mini',
    api_key: '',
    endpoint: '',
  }

  function updatePE(patch: Partial<Settings['personality_engine']>) {
    onChange({ personality_engine: { ...pe, ...patch } })
  }

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <h3 className="text-sm font-heading font-semibold text-text-muted uppercase tracking-wide">
          AI & Personality
        </h3>

        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={pe.enabled ?? false}
            onCheckedChange={(checked: boolean) => updatePE({ enabled: checked })}
          />
          <span className="text-sm">Enable personality engine</span>
        </label>

        <div className="space-y-2">
          <Label htmlFor="pe_provider">Provider</Label>
          <select
            id="pe_provider"
            value={pe.provider ?? 'openai'}
            onChange={(e) => updatePE({ provider: e.target.value })}
            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm cursor-pointer"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="pe_api_key">API Key</Label>
          <Input
            id="pe_api_key"
            type="password"
            value={pe.api_key ?? ''}
            onChange={(e) => updatePE({ api_key: e.target.value })}
            placeholder="sk-..."
          />
        </div>

        {pe.provider === 'custom' && (
          <div className="space-y-2">
            <Label htmlFor="pe_endpoint">Endpoint</Label>
            <Input
              id="pe_endpoint"
              value={pe.endpoint ?? ''}
              onChange={(e) => updatePE({ endpoint: e.target.value })}
              placeholder="https://api.example.com/v1"
            />
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="pe_model">Model</Label>
          <Input
            id="pe_model"
            value={pe.model ?? ''}
            onChange={(e) => updatePE({ model: e.target.value })}
            placeholder="gpt-4o-mini"
          />
        </div>
      </section>
    </div>
  )
}
