import * as React from "react"
import { createPortal } from "react-dom"
import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"

interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  value: string
  options: SelectOption[]
  onChange: (value: string) => void
  className?: string
  id?: string
}

export function Select({ value, options, onChange, className, id }: SelectProps) {
  const [open, setOpen] = React.useState(false)
  const triggerRef = React.useRef<HTMLButtonElement>(null)
  const dropdownRef = React.useRef<HTMLDivElement>(null)
  const [pos, setPos] = React.useState({ top: 0, left: 0, width: 0 })

  const selected = options.find((o) => o.value === value)

  React.useEffect(() => {
    if (!open) return

    // Position the dropdown below the trigger
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPos({ top: rect.bottom + 4, left: rect.left, width: rect.width })
    }

    function handleClick(e: MouseEvent) {
      const target = e.target as Node
      if (
        triggerRef.current?.contains(target) ||
        dropdownRef.current?.contains(target)
      ) return
      setOpen(false)
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [open])

  return (
    <>
      <button
        ref={triggerRef}
        id={id}
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex h-8 w-full items-center justify-between rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm cursor-pointer transition-colors outline-none focus:border-ring focus:ring-3 focus:ring-ring/50",
          className
        )}
      >
        <span>{selected?.label ?? value}</span>
        <ChevronDown className="h-3.5 w-3.5 opacity-50" />
      </button>
      {open && createPortal(
        <div
          ref={dropdownRef}
          className="fixed z-50 rounded-lg border border-border bg-surface shadow-md"
          style={{ top: pos.top, left: pos.left, width: pos.width }}
        >
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => {
                onChange(opt.value)
                setOpen(false)
              }}
              className={cn(
                "flex w-full items-center px-2.5 py-1.5 text-sm cursor-pointer transition-colors first:rounded-t-lg last:rounded-b-lg",
                opt.value === value
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-text hover:bg-border/50"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>,
        document.body
      )}
    </>
  )
}
