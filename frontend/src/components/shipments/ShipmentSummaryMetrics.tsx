import { LogisticsIcon, type LogisticsIconName } from '../common/LogisticsIcon'

interface MetricCardProps {
  label: string
  count: number
  icon: LogisticsIconName
  variant?: 'slate' | 'blue' | 'emerald' | 'amber' | 'rose'
}

export function ShipmentSummaryMetrics({
  total = 0,
  inTransit = 0,
  delivered = 0,
  incidences = 0,
}: {
  total?: number
  inTransit?: number
  delivered?: number
  incidences?: number
}) {
  const cards: MetricCardProps[] = [
    {
      label: 'Total de envíos',
      count: total,
      icon: 'package',
      variant: 'slate',
    },
    {
      label: 'En tránsito',
      count: inTransit,
      icon: 'truck',
      variant: 'blue',
    },
    {
      label: 'Entregados',
      count: delivered,
      icon: 'check',
      variant: 'emerald',
    },
    {
      label: 'Con incidencia',
      count: incidences,
      icon: 'alert',
      variant: 'amber',
    },
  ]

  const colorStyles = {
    slate: 'bg-slate-100 text-slate-700',
    blue: 'bg-blue-50 text-blue-700',
    emerald: 'bg-emerald-50 text-emerald-700',
    amber: 'bg-amber-50 text-amber-700',
    rose: 'bg-rose-50 text-rose-700',
  }

  return (
    <section className="grid grid-cols-2 gap-3.5 sm:grid-cols-4" aria-label="Indicadores de envíos">
      {cards.map((card) => (
        <div
          key={card.label}
          className="flex h-[68px] items-center gap-3 rounded-xl border border-slate-200/90 bg-white px-3.5 shadow-2xs transition-colors hover:border-slate-300"
        >
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg font-medium ${colorStyles[card.variant ?? 'slate']}`}
            aria-hidden="true"
          >
            <LogisticsIcon name={card.icon} size={20} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[11px] font-medium text-[#667085]">
              {card.label}
            </p>
            <p className="text-lg font-bold tracking-tight text-[#172033]">
              {card.count.toLocaleString()}
            </p>
          </div>
        </div>
      ))}
    </section>
  )
}
