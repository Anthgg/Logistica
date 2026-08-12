import { StatusPill, SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows, KeyValueGrid } from './ui/Primitives'
import { dataQualityLabel, dataQualityTone, formatServerTime, formatServerDateTime } from '../utils/format'
import type { ReceivingScanPreparation, UnloadingEquipmentAssignment } from '../types/inbound-docks'

export function ReceivingScanPreparationPanel({
  prep,
  loading,
  error,
}: {
  prep: ReceivingScanPreparation | undefined
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <SectionPanel
        title="Preparación para Fase 039"
        description="Recepción por producto, lote, serie y cantidad se realizará en la Fase 039."
      >
        <SkeletonRows rows={3} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel
        title="Preparación para Fase 039"
        description="Recepción por producto, lote, serie y cantidad se realizará en la Fase 039."
      >
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!prep) {
    return (
      <SectionPanel
        title="Preparación para Fase 039"
        description="Recepción por producto, lote, serie y cantidad se realizará en la Fase 039."
      >
        <EmptyPanel title="Sin preparación" description="La descarga operativa aún no se ha finalizado." />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel
      title="Preparación para Fase 039"
      description="Solo lectura. No se registran cantidades recibidas desde esta fase."
    >
      <div className="flex flex-wrap items-center gap-2">
        <StatusPill tone={prep.is_ready_for_receiving ? 'success' : 'warning'}>
          {prep.is_ready_for_receiving ? 'Lista para Fase 039' : 'Pendiente'}
        </StatusPill>
        <StatusPill tone={dataQualityTone(prep.data_quality)}>
          {dataQualityLabel(prep.data_quality)}
        </StatusPill>
      </div>
      <div className="mt-3">
        <KeyValueGrid
          items={[
            { label: 'Operación', value: prep.operation_id },
            { label: 'Muelle', value: `${prep.dock_code} — ${prep.dock_name}` },
            { label: 'CPV', value: prep.cpv_code ?? '—' },
            { label: 'CIT', value: prep.cit_code ?? '—' },
            { label: 'Proveedor', value: prep.supplier?.name ?? '—' },
            { label: 'Transportista', value: prep.carrier?.name ?? '—' },
            { label: 'Vehículo', value: prep.vehicle?.plate ?? '—' },
            { label: 'OC', value: prep.po_codes?.length ? prep.po_codes.join(', ') : '—' },
            { label: 'Líneas esperadas', value: prep.expected_lines_count ?? '—' },
            { label: 'Pallets', value: prep.pallets ?? '—' },
            { label: 'Bultos', value: prep.packages ?? '—' },
            { label: 'Peso', value: prep.weight ?? '—' },
            { label: 'Precinto', value: prep.seal_number ?? '—' },
            { label: 'Inicio descarga', value: prep.unloading_started_at ? formatServerTime(prep.unloading_started_at) : '—' },
            { label: 'Fin descarga', value: prep.unloading_completed_at ? formatServerTime(prep.unloading_completed_at) : '—' },
            { label: 'Documentos', value: prep.documents?.length ? `${prep.documents.length} adjunto(s)` : '—' },
          ]}
        />
      </div>
      {prep.warnings && prep.warnings.length > 0 && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-amber-700">
          <p className="text-[11px] font-semibold">Advertencias</p>
          <ul className="list-disc pl-4 text-[11px]">
            {prep.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}
      {prep.blocking_issues && prep.blocking_issues.length > 0 && (
        <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
          <p className="text-[11px] font-semibold">Bloqueos</p>
          <ul className="list-disc pl-4 text-[11px]">
            {prep.blocking_issues.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="mt-3 rounded-lg border border-indigo-200 bg-indigo-50/40 p-2 text-[11px] text-indigo-700">
        Descarga operativa finalizada. La recepción por producto, lote, serie y cantidad se realizará en la Fase 039.
      </p>
    </SectionPanel>
  )
}

export function UnloadingEquipmentPanel({
  equipment,
  loading,
  error,
}: {
  equipment: UnloadingEquipmentAssignment[] | undefined
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <SectionPanel title="Equipo" description="Solo declarado. No se crea ni se mantiene.">
        <SkeletonRows rows={3} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Equipo" description="Solo declarado. No se crea ni se mantiene.">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!equipment?.length) {
    return (
      <SectionPanel title="Equipo" description="Solo declarado. No se crea ni se mantiene.">
        <EmptyPanel title="Sin equipo" description="No hay equipo declarado para esta operación." />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel title="Equipo" description="Solo declarado. No se crea ni se mantiene.">
      <ul className="space-y-2 text-xs">
        {equipment.map((e) => (
          <li key={e.id} className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-slate-800">{e.equipment_type}</p>
                <p className="text-[11px] text-slate-500">{e.equipment_identifier ?? '—'}</p>
              </div>
              <StatusPill tone={e.released_at ? 'muted' : 'info'}>
                {e.released_at ? 'Liberado' : 'Asignado'}
              </StatusPill>
            </div>
            <p className="text-[11px] text-slate-600">Estado declarado: {e.status_declared}</p>
            {e.responsible && <p className="text-[10px] text-slate-500">Responsable: {e.responsible.display_name}</p>}
            <p className="text-[10px] text-slate-500">Asignado: {formatServerDateTime(e.assigned_at)}</p>
            {e.released_at && <p className="text-[10px] text-slate-500">Liberado: {formatServerDateTime(e.released_at)}</p>}
          </li>
        ))}
      </ul>
    </SectionPanel>
  )
}

export function DockOperationHistoryTimeline({
  events,
}: {
  events: Array<{
    id: string
    event_type: string
    occurred_at: string
    actor: { display_name: string } | null
    previous_status: string | null
    new_status: string | null
    reason: string | null
    result: string | null
  }>
}) {
  if (!events.length) {
    return (
      <SectionPanel title="Historial" description="Eventos de la operación">
        <EmptyPanel title="Sin historial" description="Aún no hay eventos registrados." />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel title="Historial" description="Eventos de la operación">
      <ol className="space-y-2 text-xs">
        {events.map((e) => (
          <li key={e.id} className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-slate-800">{e.event_type}</p>
              <p className="font-mono text-[11px] text-slate-500">{formatServerDateTime(e.occurred_at)}</p>
            </div>
            <p className="text-[11px] text-slate-600">
              {e.previous_status ?? '—'} → {e.new_status ?? '—'}
            </p>
            <p className="text-[11px] text-slate-600">Actor: {e.actor?.display_name ?? '—'}</p>
            {e.reason && <p className="text-[11px] text-slate-600">Motivo: {e.reason}</p>}
            {e.result && <p className="text-[11px] text-slate-600">Resultado: {e.result}</p>}
          </li>
        ))}
      </ol>
    </SectionPanel>
  )
}
