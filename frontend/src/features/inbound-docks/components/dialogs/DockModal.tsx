import { type ReactNode, useEffect, useRef } from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { clsx } from 'clsx'
import { LogisticsIcon } from '../../../../components/common/LogisticsIcon'

const SIZE_CLASSES = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
} as const

export type ModalSize = keyof typeof SIZE_CLASSES

export interface DockModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children: ReactNode
  footer?: ReactNode
  size?: ModalSize
}

export function DockModal({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  size = 'md',
}: DockModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (open) {
      const id = window.setTimeout(() => closeRef.current?.focus(), 30)
      return () => window.clearTimeout(id)
    }
    return undefined
  }, [open])
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm" />
        <DialogPrimitive.Content
          className={clsx(
            'fixed left-1/2 top-1/2 z-50 flex max-h-[92vh] w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl',
            SIZE_CLASSES[size],
          )}
        >
          <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div className="space-y-1">
              <DialogPrimitive.Title className="text-base font-bold text-slate-900">
                {title}
              </DialogPrimitive.Title>
              {description && (
                <DialogPrimitive.Description className="text-xs text-slate-500">
                  {description}
                </DialogPrimitive.Description>
              )}
            </div>
            <DialogPrimitive.Close
              ref={closeRef}
              aria-label="Cerrar"
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]"
            >
              <LogisticsIcon name="x" size={16} />
            </DialogPrimitive.Close>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-4 text-sm text-slate-700">
            {children}
          </div>
          {footer && (
            <div className="flex flex-wrap items-center justify-end gap-2 border-t border-slate-100 bg-slate-50/50 px-5 py-3">
              {footer}
            </div>
          )}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
