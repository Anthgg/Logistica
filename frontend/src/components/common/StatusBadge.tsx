import type { ReactNode } from 'react'
import { useTranslations } from '../../hooks/useTranslations'
import type { TranslationNamespace } from '../../types/i18n'

const positive = new Set(['active', 'completed', 'delivered', 'resolved', 'accepted', 'picked_up', 'warehouse_received', 'out_for_delivery'])
const danger   = new Set(['inactive', 'cancelled', 'critical', 'urgent', 'delayed', 'returned'])
const warning  = new Set(['pending', 'pending_pickup', 'planned', 'investigating', 'high', 'open'])

function getVariant(val: string) {
  if (positive.has(val)) return 'emerald'
  if (danger.has(val))   return 'rose'
  if (warning.has(val))  return 'amber'
  return 'slate'
}

const variantMap = {
  emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  rose:    'border-rose-200   bg-rose-50   text-rose-700',
  amber:   'border-amber-200  bg-amber-50  text-amber-700',
  slate:   'border-slate-200  bg-slate-50  text-slate-600',
}

const dotMap = {
  emerald: 'bg-emerald-500',
  rose:    'bg-rose-500',
  amber:   'bg-amber-500',
  slate:   'bg-slate-400',
}

export function StatusBadge({
  value = '',
  children,
  namespace = 'status',
}: {
  value?: string
  children?: ReactNode
  namespace?: TranslationNamespace
}) {
  const { translate } = useTranslations()
  const key = (value || '').toLowerCase()
  const variant = getVariant(key)
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium leading-none ${variantMap[variant]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${dotMap[variant]}`} aria-hidden="true" />
      {children ?? translate(namespace, key, value)}
    </span>
  )
}

export function PriorityBadge({
  value = '',
  children,
}: {
  value?: string
  children?: ReactNode
}) {
  const { translate } = useTranslations()
  const key = (value || '').toLowerCase()
  const classes: Record<string, string> = {
    urgent: 'border-rose-200   bg-rose-50   text-rose-700',
    high:   'border-amber-200  bg-amber-50  text-amber-700',
    medium: 'border-blue-200   bg-blue-50   text-blue-700',
    normal: 'border-slate-200  bg-slate-50  text-slate-600',
    low:    'border-slate-200  bg-slate-50  text-slate-500',
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${classes[key] ?? classes.normal}`}>
      {children ?? translate('priority', key, value)}
    </span>
  )
}
