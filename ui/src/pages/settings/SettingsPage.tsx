import { useCallback, useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Save } from 'lucide-react'
import { useBridge, useBridgeEvent } from '@/bridge/context'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { GeneralTab } from './GeneralTab'
import { BehaviorsTab } from './BehaviorsTab'
import { IntegrationsTab } from './IntegrationsTab'
import { PersonalityTab } from './PersonalityTab'
import type { Settings } from '@/bridge/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function deepMerge(base: any, patch: any): any {
  const result = { ...base }
  for (const key in patch) {
    const patchVal = patch[key]
    const baseVal = result[key]
    if (
      patchVal !== null &&
      typeof patchVal === 'object' &&
      !Array.isArray(patchVal) &&
      baseVal !== null &&
      typeof baseVal === 'object' &&
      !Array.isArray(baseVal)
    ) {
      result[key] = deepMerge(baseVal, patchVal)
    } else {
      result[key] = patchVal
    }
  }
  return result
}

export function SettingsPage() {
  const { send } = useBridge()
  const [settings, setSettings] = useState<Settings | null>(null)
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const originalRef = useRef<Settings | null>(null)

  // Load settings on mount
  useEffect(() => {
    send('settings.load')
  }, [send])

  // Subscribe to settings data
  useBridgeEvent('settings.data', useCallback((data: Settings) => {
    setSettings(data)
    originalRef.current = data
    setDirty(false)
  }, []))

  // Subscribe to save confirmation
  useBridgeEvent('settings.saved', useCallback(() => {
    setSaving(false)
    setDirty(false)
    if (settings) {
      originalRef.current = settings
    }
  }, [settings]))

  function handleChange(patch: Partial<Settings>) {
    if (!settings) return
    const updated = deepMerge(settings, patch)
    setSettings(updated)
    setDirty(true)
  }

  function handleSave() {
    if (!settings) return
    setSaving(true)
    send('settings.save', { settings })
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-text-muted text-sm">Loading settings...</p>
      </div>
    )
  }

  return (
    <Tabs defaultValue="general">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        {/* Sticky header bar */}
        <div className="sticky top-0 z-10 bg-white px-5 pt-5 pb-0 shadow-[0_2px_8px_rgb(44_24_16/0.06)]">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-heading font-bold text-text">Settings</h1>
            {dirty && (
              <Button
                onClick={handleSave}
                disabled={saving}
                className="cursor-pointer gap-1.5"
                size="sm"
              >
                <Save size={14} />
                {saving ? 'Saving...' : 'Save'}
              </Button>
            )}
          </div>
          <TabsList variant="line" className="w-full">
            <TabsTrigger value="general" className="cursor-pointer">General</TabsTrigger>
            <TabsTrigger value="behaviors" className="cursor-pointer">Behaviors</TabsTrigger>
            <TabsTrigger value="integrations" className="cursor-pointer">Integrations</TabsTrigger>
            <TabsTrigger value="personality" className="cursor-pointer">AI</TabsTrigger>
          </TabsList>
        </div>

        {/* Content — main handles the scroll */}
        <div className="p-4">
          <TabsContent value="general">
            <GeneralTab settings={settings} onChange={handleChange} />
          </TabsContent>

          <TabsContent value="behaviors">
            <BehaviorsTab settings={settings} onChange={handleChange} />
          </TabsContent>

          <TabsContent value="integrations">
            <IntegrationsTab settings={settings} onChange={handleChange} />
          </TabsContent>

          <TabsContent value="personality">
            <PersonalityTab settings={settings} onChange={handleChange} />
          </TabsContent>
        </div>
      </motion.div>
    </Tabs>
  )
}
