import { useParams } from 'react-router-dom'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { ReceptionDifferenceIntegrity } from '../types/reception-differences'

export function ReceptionDifferenceIntegrityPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const auth = useLogisticsPermissions()

  const integrityQuery = useQuery<ReceptionDifferenceIntegrity>(
    ['reception-difference-integrity', caseId],
    `/logistics/reception-difference-cases/${caseId}/integrity`,
    undefined,
    { enabled: !!caseId },
  )

  if (!auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.viewIntegrity)) {
    return (
      <div className="page">
        <div className="panel p-6 text-center text-sm text-slate-500">
          No tienes permisos para ver la integridad.
        </div>
      </div>
    )
  }

  const integrity = integrityQuery.data

  return (
    <div className="page">
      <h1 className="mb-4 text-lg font-bold text-slate-800">Integridad</h1>

      {!integrity ? (
        <div className="panel p-8 text-center text-sm text-slate-400">
          No se encontró información de integridad.
        </div>
      ) : (
        <div className="panel p-4 text-xs space-y-2">
          <InfoRow label="Algoritmo" value={integrity.algorithm} />
          <InfoRow label="Estado" value={integrity.status} />
          <InfoRow label="Última verificación" value={integrity.last_verified_at ?? '—'} />
          <HashRow label="Fuente" hash={integrity.source_hash} />
          <HashRow label="Ítems" hash={integrity.items_hash} />
          <HashRow label="Evidencias" hash={integrity.evidence_hash} />
          <HashRow label="Responsables" hash={integrity.responsibilities_hash} />
          <HashRow label="Revisión" hash={integrity.review_hash} />
          <HashRow label="Aprobación" hash={integrity.approval_hash} />
          <HashRow label="Reconocimiento" hash={integrity.acknowledgement_hash} />
          <HashRow label="Snapshot" hash={integrity.snapshot_hash} />
          <HashRow label="PDF" hash={integrity.pdf_hash} />
        </div>
      )}
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-32 font-semibold text-slate-600">{label}:</span>
      <span className="text-slate-800">{value}</span>
    </div>
  )
}

function HashRow({ label, hash }: { label: string; hash: string | null }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-32 font-semibold text-slate-600">{label}:</span>
      <span className="font-mono text-[10px] text-slate-500">{hash ?? '—'}</span>
    </div>
  )
}
