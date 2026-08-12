import type { ReactNode } from 'react'

interface AlertProps {
  variant?: 'error' | 'success' | 'info' | 'warning'
  title?: string
  children: ReactNode
  onDismiss?: () => void
}

const variantClasses = {
  error:   'bg-[#FFF5F5] border-[#FAE0E1] text-danger',
  success: 'bg-emerald-xlight border-emerald-light text-emerald',
  info:    'bg-primary-xlight border-primary-light text-primary',
  warning: 'bg-amber-xlight border-amber-light text-amber',
}

export function Alert({ variant = 'info', title, children, onDismiss }: AlertProps) {
  return (
    <div
      className={`px-3.5 py-3 rounded-[10px] border text-xs font-medium flex items-start gap-2 justify-between ${variantClasses[variant]}`}
      role={variant === 'error' ? 'alert' : 'status'}
      aria-live={variant === 'error' ? 'assertive' : 'polite'}
    >
      <div className="flex flex-col gap-1">
        {title && <strong className="text-[13px] font-bold">{title}</strong>}
        <div>{children}</div>
      </div>
      {onDismiss && (
        <button
          type="button"
          className="text-current opacity-50 hover:opacity-80 transition-opacity text-base leading-none cursor-pointer border-none bg-transparent font-sans"
          onClick={onDismiss}
          aria-label="Cerrar mensaje"
        >
          ×
        </button>
      )}
    </div>
  )
}
