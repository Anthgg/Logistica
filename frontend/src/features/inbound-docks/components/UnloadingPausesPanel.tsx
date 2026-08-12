import { StatusPill, SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows } from './ui/Primitives'
import { formatServerTime, formatSecondsApprox, severityLabel } from '../utils/format'
import type { UnloadingPause } from '../types/inbound-docks'

export function UnloadingPausesPanel({
  pauses,
  loading,
  error,
}: {
  pauses: UnloadingPause[] | undefined
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <SectionPanel title="Pausas" description="Historial de pausas operativas">
        <SkeletonRows rows={3} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Pausas" description="Historial de pausas operativas">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!pauses?.length) {
    return (
      <SectionPanel title="Pausas" description="Historial de pausas operativas">
        <EmptyPanel title="Sin pausas" description="La operación no registra pausas todavía." />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel title="Pausas" description="Historial de pausas operativas">
      <ul className="space-y-2 text-xs">
        {pauses.map((p) => (
          <li key={p.id} className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-slate-800">{p.reason_label}</p>
                <p className="text-[11px] text-slate-500">Motivo: {p.reason}</p>
              </div>
              <div className="flex items-center gap-2">
                <StatusPill tone={p.is_active ? 'warning' : 'muted'}>{p.is_active ? 'Activa' : 'Cerrada'}</StatusPill>
                <StatusPill tone={p.severity === 'CRITICAL' ? 'danger' : p.severity === 'HIGH' ? 'warning' : 'info'}>
                  {severityLabel(p.severity)}
                </StatusPill>
              </div>
            </div>
            <p className="mt-1 text-[11px] text-slate-600">
              Inicio: {formatServerTime(p.started_at)} · Fin: {p.ended_at ? formatServerTime(p.ended_at) : '—'}
            </p>
            {p.comment && <p className="text-[11px] text-slate-600">Comentario: {p.comment}</p>}
            {p.evidence_file_id && <p className="text-[11px] text-slate-600">Evidencia: {p.evidence_file_id}</p>}
            {p.responsible_informed && (
              <p className="text-[10px] text-slate-500">Informado: {p.responsible_informed.display_name}</p>
            )}
            <p className="text-[10px] text-slate-500">
              Duración registrada: {formatSecondsApprox(p.duration_seconds)}
            </p>
            <p className="text-[10px] text-slate-500">Registrada: {formatServerTime(p.started_at)}</p>
          </li>
        ))}
      </ul>
    </SectionPanel>
  )
}
