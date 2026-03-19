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

    function handleClick(e: MouseEvent) {
      const target = e.target as Node
      if (
        triggerRef.current?.contains(target) ||
        dropdownRef.current?.contains(target)
      ) return
      setOpen(false)
    }

    // NEW: Close the dropdown on scroll or resize to prevent visual detaching
    function handleLayoutChange() {
      setOpen(false)
    }

    document.addEventListener("mousedown", handleClick)
    // We use the capture phase (true) here so it catches scrolling inside ANY inner div, not just the window
    window.addEventListener("scroll", handleLayoutChange, true)
    window.addEventListener("resize", handleLayoutChange)

    return () => {
      document.removeEventListener("mousedown", handleClick)
      window.removeEventListener("scroll", handleLayoutChange, true)
      window.removeEventListener("resize", handleLayoutChange)
    }
  }, [open])

  function handleOpen() {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPos({
        top: rect.bottom + 4,
        left: rect.left,
        width: rect.width
      })
    }
    setOpen((o) => !o)
  }

  return (
    <>
      <button
        ref={triggerRef}
        id={id}
        type="button"
        onClick={handleOpen}
        className={cn(
          "flex h-8 w-full items-center justify-between rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm cursor-pointer transition-colors outline-none focus:border-ring focus:ring-3 focus:ring-ring/50",
          className
        )}
      >
        <span>{selected?.label ?? value}</span>
        <ChevronDown className="h-3.5 w-3.5 opacity-50" />
      </button>
      {open && createPortal(
        // Outer div: positioned anchor — may stretch due to a WebKit bug where
        // height:auto on position:fixed resolves to (viewport − top) when body
        // has min-height:100vh.  It carries no visual styles so the stretch is
        // invisible.  pointer-events:none lets clicks in the blank area fall
        // through to the document and trigger the close handler.
        <div
          style={{
            position: 'fixed',
            zIndex: 9999,
            top: pos.top,
            left: pos.left,
            width: pos.width,
            pointerEvents: 'none',
          }}
        >
          {/* Inner div: normal-flow block — never affected by the WebKit
              height bug, always sizes to its content. */}
          <div
            ref={dropdownRef}
            className="rounded-lg border border-border bg-surface shadow-md"
            style={{
              maxHeight: '250px',
              overflowY: 'auto',
              pointerEvents: 'auto',
            }}
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
                  "flex w-full items-center px-2.5 py-1.5 text-sm cursor-pointer transition-colors",
                  opt.value === value
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-text hover:bg-border/50"
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>,
        document.body
      )}
    </>
  )
}