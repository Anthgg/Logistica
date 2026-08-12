import type { ReactNode } from 'react'
import { useTranslations } from '../../hooks/useTranslations'

export function ShipmentStatusBadge({
  value,
  children,
}: {
  value: string
  children?: ReactNode
}) {
  const { translate } = useTranslations()
  const key = value.toLowerCase()

  const positive = new Set([
    'active',
    'completed',
    'delivered',
    'resolved',
    'accepted',
    'picked_up',
    'warehouse_received',
    'out_for_delivery',
  ])
  const danger = new Set([
    'inactive',
    'cancelled',
    'critical',
    'urgent',
    'delayed',
    'returned',
  ])
  const warning = new Set([
    'pending',
    'pending_pickup',
    'planned',
    'investigating',
    'high',
    'open',
  ])

  let variant = 'slate'
  if (positive.has(key)) variant = 'emerald'
  else if (danger.has(key)) variant = 'rose'
  else if (warning.has(key)) variant = 'amber'

  const variantMap = {
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    rose: 'border-rose-200 bg-rose-50 text-rose-700',
    amber: 'border-amber-200 bg-amber-50 text-amber-700',
    slate: 'border-slate-200 bg-slate-50 text-slate-700',
  }

  const dotMap = {
    emerald: 'bg-emerald-500',
    rose: 'bg-rose-500',
    amber: 'bg-amber-500',
    slate: 'bg-slate-400',
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold leading-tight ${variantMap[variant as keyof typeof variantMap]}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full shrink-0 ${dotMap[variant as keyof typeof dotMap]}`}
        aria-hidden="true"
      />
      {children ?? translate('status', key, value)}
    </span>
  )
}

export function ShipmentPriorityBadge({
  value,
  children,
}: {
  value: string
  children?: ReactNode
}) {
  const { translate } = useTranslations()
  const key = value.toLowerCase()

  const classes: Record<string, string> = {
    urgent: 'border-rose-200 bg-rose-50 text-rose-700 font-bold',
    high: 'border-amber-200 bg-amber-50 text-amber-700 font-semibold',
    normal: 'border-blue-200 bg-blue-50 text-blue-700 font-medium',
    low: 'border-slate-200 bg-slate-50 text-slate-600 font-medium',
  }

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs ${classes[key] ?? classes.normal}`}
    >
      {children ?? translate('priority', key, value)}
    </span>
  )
}
