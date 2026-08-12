import type { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-col items-stretch justify-between gap-3 border-b border-[#EEF2F5] pt-4 pb-3 sm:flex-row sm:items-center">
      <div>
        {eyebrow && (
          <p className="text-[10px] font-bold text-orange uppercase tracking-widest mb-1">
            {eyebrow}
          </p>
        )}
        <h1 className="text-[clamp(20px,1.8vw,24px)] font-bold text-ink tracking-tight leading-none">
          {title}
        </h1>
        {description && (
          <p className="text-xs text-muted mt-1">{description}</p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center justify-start gap-2 sm:justify-end">{actions}</div>}
    </header>
  )
}
