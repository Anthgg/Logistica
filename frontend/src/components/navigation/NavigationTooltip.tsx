import React, { useState } from 'react'
import { createPortal } from 'react-dom'

interface NavigationTooltipProps {
  label: string
  shortcut?: string
  children: React.ReactElement
  showLabelPermanent?: boolean
}

interface TooltipPos {
  x: number
  bottom: number
}

export function NavigationTooltip({
  label,
  shortcut,
  children,
  showLabelPermanent = false,
}: NavigationTooltipProps) {
  const [pos, setPos] = useState<TooltipPos | null>(null)

  if (showLabelPermanent) return children

  const onEnter = (e: React.MouseEvent<HTMLElement>) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setPos({
      x: Math.round(rect.left + rect.width / 2),
      bottom: Math.round(window.innerHeight - rect.top + 10),
    })
    const orig = (children.props as React.HTMLAttributes<HTMLElement>).onMouseEnter
    if (orig) orig(e)
  }

  const onLeave = (e: React.MouseEvent<HTMLElement>) => {
    setPos(null)
    const orig = (children.props as React.HTMLAttributes<HTMLElement>).onMouseLeave
    if (orig) orig(e)
  }

  // Sin wrapper div — handlers directamente en el hijo
  const enhancedChild = React.cloneElement(
    children,
    { onMouseEnter: onEnter, onMouseLeave: onLeave } as Partial<React.HTMLAttributes<HTMLElement>>,
  )

  return (
    <>
      {enhancedChild}

      {pos !== null &&
        createPortal(
          <div
            role="tooltip"
            className="pointer-events-none fixed z-[99999] flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-slate-600/50 bg-slate-950 px-2.5 py-1.5 text-[11px] font-medium text-slate-100 shadow-xl"
            style={{
              left: pos.x,
              bottom: pos.bottom,
              transform: 'translateX(-50%)',
            }}
          >
            <span>{label}</span>

            {shortcut && (
              <kbd className="rounded border border-slate-700 bg-slate-800 px-1 py-px font-mono text-[9px] text-slate-400 not-italic">
                {shortcut}
              </kbd>
            )}

            {/* Triángulo CSS puro apuntando hacia abajo */}
            <span
              aria-hidden
              style={{
                position: 'absolute',
                top: '100%',
                left: '50%',
                transform: 'translateX(-50%)',
                width: 0,
                height: 0,
                borderLeft: '5px solid transparent',
                borderRight: '5px solid transparent',
                borderTop: '5px solid #020617', /* slate-950 */
              }}
            />
          </div>,
          document.body,
        )}
    </>
  )
}
