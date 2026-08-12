import type { GateCheckInCapabilities, GatePhotoEvidence } from '../types/gate-control'
import { evidenceTypeLabel } from '../format'
import { EmptyState, StatusPill } from './ui'

export function GateEvidenceGallery({
  photos, capabilities,
}: {
  photos: GatePhotoEvidence[]
  capabilities: GateCheckInCapabilities | null
  checkInId: string
  onChanged: () => void
}) {
  if (photos.length === 0) return <EmptyState title="Sin evidencias fotográficas" />

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">Los archivos sensibles requieren permiso adicional. No se persisten URLs firmadas.</p>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {photos.map((p) => {
          const canView = !p.is_sensitive || (capabilities?.can_view_sensitive_photo && p.can_view)
          return (
            <div key={p.id} className="rounded-lg border border-slate-200 p-2 text-xs">
              <div className="font-semibold">{evidenceTypeLabel(p.evidence_type)}</div>
              <div className="mt-1 text-slate-500">{p.file.name}</div>
              <div className="text-[10px] text-slate-400">{new Date(p.captured_at).toLocaleString('es-PE')}</div>
              <div className="mt-1 flex items-center gap-1">
                {p.is_sensitive && <StatusPill tone="danger">Restringido</StatusPill>}
                {canView ? <StatusPill tone="success">Visible</StatusPill> : <StatusPill tone="muted">Sin acceso</StatusPill>}
              </div>
              <div className="mt-1 font-mono text-[10px] text-slate-400">{p.file.partial_hash?.slice(0, 12) ?? '—'}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}