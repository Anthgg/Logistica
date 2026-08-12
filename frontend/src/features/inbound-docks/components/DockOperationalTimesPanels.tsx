import { SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows, KeyValueGrid, StatusPill } from './ui/Primitives'
import {
  dataQualityLabel,
  dataQualityTone,
  formatServerTime,
  formatSecondsApprox,
} from '../utils/format'
import type {
  DockOperationalMetrics,
  DockOperationalTimes,
  OperationalTimeQualityStatus,
} from '../types/inbound-docks'

export function DockOperationalTimesPanel({
  times,
  loading,
  error,
}: {
  times: DockOperationalTimes | undefined
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <SectionPanel title="Tiempos operativos" description="Eventos autoritativos">
        <SkeletonRows rows={4} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Tiempos operativos" description="Eventos autoritativos">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!times) {
    return (
      <SectionPanel title="Tiempos operativos" description="Eventos autoritativos">
        <EmptyPanel title="Sin tiempos" />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel
      title="Tiempos operativos"
      description="Eventos autoritativos del backend"
    >
      <KeyValueGrid
        items={[
          { label: 'Llegada a garita', value: times.gate_arrival_at ? formatServerTime(times.gate_arrival_at) : '—' },
          { label: 'Liberación garita', value: times.gate_clearance_at ? formatServerTime(times.gate_clearance_at) : '—' },
          { label: 'Entrada a cola', value: times.queue_entry_at ? formatServerTime(times.queue_entry_at) : '—' },
          { label: 'Asignación', value: times.assigned_at ? formatServerTime(times.assigned_at) : '—' },
          { label: 'Movimiento', value: times.movement_started_at ? formatServerTime(times.movement_started_at) : '—' },
          { label: 'Llegada al muelle', value: times.dock_arrival_at ? formatServerTime(times.dock_arrival_at) : '—' },
          { label: 'Inicio descarga', value: times.unloading_started_at ? formatServerTime(times.unloading_started_at) : '—' },
          { label: 'Fin descarga', value: times.unloading_completed_at ? formatServerTime(times.unloading_completed_at) : '—' },
          { label: 'Liberación muelle', value: times.dock_released_at ? formatServerTime(times.dock_released_at) : '—' },
        ]}
      />
      {times.missing_events && times.missing_events.length > 0 && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-amber-700">
          <p className="text-[11px] font-semibold">Eventos faltantes</p>
          <ul className="list-disc pl-4 text-[11px]">
            {times.missing_events.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </div>
      )}
      {times.pauses && times.pauses.length > 0 && (
        <div className="mt-3">
          <p className="text-[11px] font-semibold text-slate-700">Pausas</p>
          <ul className="list-disc pl-4 text-[11px] text-slate-600">
            {times.pauses.map((p) => (
              <li key={p.id}>
                {p.reason_label} · {p.started_at ? formatServerTime(p.started_at) : '—'} → {p.ended_at ? formatServerTime(p.ended_at) : '—'} · {formatSecondsApprox(p.duration_seconds)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </SectionPanel>
  )
}

export function DockOperationMetricsPanel({
  metrics,
  loading,
  error,
}: {
  metrics: DockOperationalMetrics | undefined
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <SectionPanel title="Métricas operativas" description="Fuente operativa, no KPI corporativo">
        <SkeletonRows rows={4} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Métricas operativas" description="Fuente operativa, no KPI corporativo">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!metrics) {
    return (
      <SectionPanel title="Métricas operativas" description="Fuente operativa, no KPI corporativo">
        <EmptyPanel title="Sin métricas" />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel title="Métricas operativas" description="Fuente operativa, no KPI corporativo">
      <KeyValueGrid
        items={[
          { label: 'Espera', value: formatSecondsApprox(metrics.wait_seconds) },
          { label: 'Movimiento', value: formatSecondsApprox(metrics.movement_seconds) },
          { label: 'Espera en muelle', value: formatSecondsApprox(metrics.dock_wait_seconds) },
          { label: 'Descarga bruta', value: formatSecondsApprox(metrics.unloading_gross_seconds) },
          { label: 'Pausas', value: formatSecondsApprox(metrics.unloading_pause_seconds) },
          { label: 'Descarga neta', value: formatSecondsApprox(metrics.unloading_net_seconds) },
          { label: 'Liberación', value: formatSecondsApprox(metrics.release_delay_seconds) },
          { label: 'Ocupación', value: formatSecondsApprox(metrics.dock_occupancy_seconds) },
          { label: 'Ciclo total', value: formatSecondsApprox(metrics.total_cycle_seconds) },
          { label: 'Control de garita', value: formatSecondsApprox(metrics.gate_control_seconds) },
        ]}
      />
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <StatusPill tone={dataQualityTone(metrics.data_quality)}>
          Calidad: {dataQualityLabel(metrics.data_quality)}
        </StatusPill>
        {metrics.impact_on_kpi && metrics.impact_on_kpi.length > 0 && (
          <ul className="list-disc pl-4 text-[11px] text-slate-600">
            {metrics.impact_on_kpi.map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        )}
      </div>
    </SectionPanel>
  )
}

export function OperationalTimeQualityPanel({
  status,
  lastValidatedAt,
  missing,
  corrected,
  impact,
}: {
  status: OperationalTimeQualityStatus | undefined
  lastValidatedAt: string | null | undefined
  missing: string[]
  corrected: string[]
  impact: string[]
}) {
  if (!status) return null
  return (
    <SectionPanel title="Calidad de tiempos" description="Resultado de integridad">
      <div className="flex flex-wrap items-center gap-2">
        <StatusPill tone={dataQualityTone(status)}>{dataQualityLabel(status)}</StatusPill>
        {lastValidatedAt && <span className="text-[11px] text-slate-500">Última validación: {formatServerTime(lastValidatedAt)}</span>}
      </div>
      {missing.length > 0 && (
        <div className="mt-2">
          <p className="text-[11px] font-semibold text-slate-700">Eventos faltantes</p>
          <ul className="list-disc pl-4 text-[11px] text-slate-600">
            {missing.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </div>
      )}
      {corrected.length > 0 && (
        <div className="mt-2">
          <p className="text-[11px] font-semibold text-slate-700">Correcciones aplicadas</p>
          <ul className="list-disc pl-4 text-[11px] text-slate-600">
            {corrected.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </div>
      )}
      {impact.length > 0 && (
        <div className="mt-2">
          <p className="text-[11px] font-semibold text-slate-700">Impacto en KPI</p>
          <ul className="list-disc pl-4 text-[11px] text-slate-600">
            {impact.map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="mt-2 rounded-lg border border-slate-200 bg-slate-50/40 p-2 text-[11px] text-slate-600">
        No se reemplaza null con cero. Las duraciones autoritativas las calcula el servidor.
      </p>
    </SectionPanel>
  )
}
