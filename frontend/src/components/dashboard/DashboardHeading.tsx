import type { ReactNode } from 'react'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface Props {
  eyebrow: string
  title: string
  description: string
  actions?: ReactNode
}

export function DashboardHeading({ eyebrow, title, description, actions }: Props) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-widest text-orange-600 leading-none mb-1">
          {eyebrow}
        </p>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 leading-tight">
          {title}
        </h1>
        <p className="text-xs text-slate-500 mt-1 leading-snug">{description}</p>
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </div>
  )
}

export function RefreshButton({ onClick, disabled }: { onClick: () => void; disabled: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 text-xs font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-blue-600 focus-visible:outline-offset-2"
    >
      <LogisticsIcon name="activity" size={14} />
      Actualizar datos
    </button>
  )
}
