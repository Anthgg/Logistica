import type { ReactNode } from 'react'
import { LogisticsIcon, type LogisticsIconName } from './LogisticsIcon'

interface EmptyStateProps {
  title: string
  description: string
  action?: ReactNode
  icon?: LogisticsIconName
}

export function EmptyState({ title, description, action, icon = 'package' }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-7 px-4 text-center text-faint">
      <div className="w-10 h-10 rounded-[10px] bg-[#F0F4F7] flex items-center justify-center text-faint" aria-hidden="true">
        <LogisticsIcon name={icon} size={22} />
      </div>
      <h3 className="text-xs font-semibold text-muted">{title}</h3>
      <p className="text-[11px] text-faint max-w-[240px] leading-relaxed">{description}</p>
      {action}
    </div>
  )
}
