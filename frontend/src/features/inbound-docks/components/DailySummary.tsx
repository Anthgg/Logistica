import { MetricCard } from '../../../components/common/MetricCard'
import type { InboundDockQueueSummary } from '../types/inbound-docks'

export function DailySummary({
  summary,
}: {
  summary: InboundDockQueueSummary | null | undefined
}) {
  if (!summary) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50/40 p-4 text-xs text-slate-500">
        Sin resumen disponible. Selecciona un almacén y espera la primera sincronización.
      </div>
    )
  }
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
      <MetricCard
        label="Vehículos esperando"
        value={summary.total_waiting}
        detail="En cola, sin muelle"
        icon="truck"
        tone="warning"
      />
      <MetricCard
        label="Muelles disponibles"
        value={summary.docks_available}
        detail="Sin operación activa"
        icon="dock"
        tone="success"
      />
      <MetricCard
        label="Muelles reservados"
        value={summary.docks_reserved}
        detail="Con asignación próxima"
        icon="calendar"
        tone="neutral"
      />
      <MetricCard
        label="Muelles ocupados"
        value={summary.docks_occupied}
        detail="Con vehículo en muelle"
        icon="truck"
        tone="primary"
      />
      <MetricCard
        label="Descargas en curso"
        value={summary.total_unloading}
        detail="Activas o en muelle"
        icon="play"
        tone="primary"
      />
      <MetricCard
        label="Descargas pausadas"
        value={summary.total_paused}
        detail="Pausa operativa"
        icon="pause"
        tone="warning"
      />
      <MetricCard
        label="Pendientes de liberar"
        value={summary.total_completed_pending_release}
        detail="Descarga finalizada"
        icon="check-square"
        tone="neutral"
      />
      <MetricCard
        label="Esperas prolongadas"
        value={summary.prolonged_waits}
        detail="Vehículos en espera extendida"
        icon="hourglass"
        tone="danger"
      />
      <MetricCard
        label="Con anomalías"
        value={summary.operations_with_anomalies}
        detail="Operaciones con alertas"
        icon="alert"
        tone="danger"
      />
      <MetricCard
        label="Datos incompletos"
        value={summary.operations_with_incomplete_data}
        detail="Operaciones con gaps de tiempo"
        icon="info"
        tone="warning"
      />
    </div>
  )
}
