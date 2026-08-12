import type { DashboardSummary } from '../../types/operations'
import { KpiCard } from './KpiCard'

interface Props {
  summary: DashboardSummary
}

export function KpiGrid({ summary }: Props) {
  return (
    <section
      className="grid w-full min-w-0 grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6"
      aria-label="Indicadores operativos clave"
    >
      <KpiCard
        icon="package"
        value={summary.total_shipments}
        label="Envíos registrados"
        detail={`${summary.pending_shipments} pendientes de proceso`}
        tone="blue"
      />
      <KpiCard
        icon="truck"
        value={summary.in_transit_shipments}
        label="En tránsito"
        detail={`${summary.routes_today} rutas programadas hoy`}
        tone="slate"
      />
      <KpiCard
        icon="check"
        value={summary.delivered_shipments}
        label="Entregas completadas"
        detail={`${summary.deliveries_today} completadas hoy`}
        tone="emerald"
      />
      <KpiCard
        icon="calendar"
        value={summary.delayed_shipments}
        label="Pedidos retrasados"
        detail="Requieren seguimiento operativo"
        tone={summary.delayed_shipments > 0 ? 'amber' : 'emerald'}
      />
      <KpiCard
        icon="alert"
        value={summary.open_incidents}
        label="Incidencias abiertas"
        detail={`${summary.critical_incidents} clasificadas críticas`}
        tone={summary.critical_incidents > 0 ? 'rose' : 'amber'}
      />
      <KpiCard
        icon="archive"
        value={summary.low_stock_items}
        label="Alertas inventario"
        detail="Ítems bajo stock mínimo"
        tone={summary.low_stock_items > 0 ? 'amber' : 'emerald'}
      />
    </section>
  )
}
