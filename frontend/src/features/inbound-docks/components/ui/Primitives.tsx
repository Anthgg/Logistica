import type { ReactNode } from 'react'
import { clsx } from 'clsx'

type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'muted'

const TONE_CLASSES: Record<Tone, string> = {
  neutral: 'bg-slate-100 text-slate-700 border-slate-200',
  info: 'bg-indigo-50 text-indigo-700 border-indigo-100',
  success: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  warning: 'bg-amber-50 text-amber-700 border-amber-100',
  danger: 'bg-rose-50 text-rose-700 border-rose-100',
  muted: 'bg-slate-50 text-slate-500 border-slate-100',
}

export function StatusPill({
  children,
  tone = 'neutral',
  className,
}: {
  children: ReactNode
  tone?: Tone
  className?: string
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold leading-none',
        TONE_CLASSES[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}

export function SectionPanel({
  title,
  description,
  children,
  actions,
  className,
}: {
  title: string
  description?: string
  children: ReactNode
  actions?: ReactNode
  className?: string
}) {
  return (
    <section className={clsx('rounded-xl border border-slate-200 bg-white p-4 shadow-xs', className)}>
      <header className="mb-3 flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-2">
        <div>
          <h2 className="text-sm font-bold text-slate-800">{title}</h2>
          {description && <p className="mt-0.5 text-xs text-slate-500">{description}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </header>
      {children}
    </section>
  )
}

export function KeyValueGrid({
  items,
}: {
  items: Array<{ label: string; value: ReactNode; mono?: boolean }>
}) {
  return (
    <dl className="grid grid-cols-1 gap-x-4 gap-y-1 text-xs sm:grid-cols-2">
      {items.map((item) => (
        <div key={item.label} className="flex flex-col">
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            {item.label}
          </dt>
          <dd className={clsx('text-sm text-slate-800', item.mono && 'font-mono')}>
            {item.value ?? '—'}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function EmptyPanel({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-200 bg-slate-50/40 px-4 py-8 text-center text-xs text-slate-500">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      {description && <p className="max-w-md">{description}</p>}
      {action}
    </div>
  )
}

export function ErrorPanel({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-2 rounded-xl border border-rose-100 bg-rose-50/40 px-4 py-6 text-center text-xs text-rose-700"
    >
      <p className="text-sm font-semibold">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-lg border border-rose-200 bg-white px-3 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-50"
        >
          Reintentar
        </button>
      )}
    </div>
  )
}

export function SkeletonRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-9 w-full animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  )
}

export function InlineTabs<T extends string>({
  tabs,
  value,
  onChange,
  className,
}: {
  tabs: Array<{ key: T; label: string }>
  value: T
  onChange: (next: T) => void
  className?: string
}) {
  return (
    <div
      className={clsx(
        'flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/60 p-1',
        className,
      )}
      role="tablist"
    >
      {tabs.map((t) => (
        <button
          key={t.key}
          type="button"
          role="tab"
          aria-selected={value === t.key}
          onClick={() => onChange(t.key)}
          className={clsx(
            'rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors',
            value === t.key
              ? 'bg-white text-[#1F4E6D] shadow-xs'
              : 'text-slate-500 hover:text-slate-800',
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}
