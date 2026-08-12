import type { ReactNode } from 'react'

interface ShipmentsPageHeaderProps {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
}

export function ShipmentsPageHeader({
  eyebrow = 'OPERACIONES / ENVÍOS',
  title = 'Gestión de envíos',
  description = 'Registra, consulta y supervisa el recorrido de cada despacho.',
  actions,
}: ShipmentsPageHeaderProps) {
  return (
    <header className="flex flex-col items-start justify-between gap-3 border-b border-slate-200/80 pb-4 pt-1 sm:flex-row sm:items-center">
      <div>
        <p className="mb-1 text-[11px] font-bold tracking-wider text-[#C85A18] uppercase">
          {eyebrow}
        </p>
        <h1 className="text-xl font-bold tracking-tight text-[#172033] sm:text-2xl">
          {title}
        </h1>
        {description && (
          <p className="mt-0.5 text-xs text-[#667085]">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex shrink-0 items-center justify-start gap-2 sm:justify-end">
          {actions}
        </div>
      )}
    </header>
  )
}
