import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { QualityQuarantineIntegrity } from '../types/quarantine'
import { StatusBadge } from '../../../components/common/StatusBadge'

const HASH_LABELS: Record<string, string> = {
  source_hash: 'Hash de recepción',
  allocations_hash: 'Hash de asignación',
  placements_hash: 'Hash de división',
  inspections_hash: 'Hash de inspección',
  decisions_hash: 'Hash de resultado',
  releases_hash: 'Hash de medición',
  rejections_hash: 'Hash de muestra',
  non_conformities_hash: 'Hash de certificado',
  evidence_hash: 'Hash de evidencia',
  history_hash: 'Hash de decisión',
  snapshot_hash: 'Cadena de eventos',
}

function TruncatedHash({ value }: { value: string | null }) {
  if (!value) {
    return <span className="text-slate-400">—</span>
  }
  const truncated = value.length > 16 ? `${value.slice(0, 8)}…${value.slice(-8)}` : value
  return (
    <span className="font-mono text-[11px] text-slate-700" title={value}>
      {truncated}
    </span>
  )
}

export function QualityQuarantineIntegrityPanel({
  caseId,
}: {
  caseId: string
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canViewIntegrity = hasPermission(LOGISTICS_PERMISSIONS.quarantine.viewIntegrity)

  const {
    data: integrity,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<QualityQuarantineIntegrity>(
    ['quarantine-integrity', caseId],
    `/logistics/quality-quarantine/cases/${caseId}/integrity`,
    undefined,
    { enabled: canViewIntegrity },
  )

  if (!canViewIntegrity) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-800">Panel de integridad</h2>
        <p className="mt-2 text-xs text-slate-500">No tiene permisos para ver la integridad.</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
      <header className="mb-3 border-b border-slate-100 pb-2">
        <h2 className="text-sm font-bold text-slate-800">Panel de integridad</h2>
        <p className="mt-0.5 text-xs text-slate-500">
          Verificación criptográfica de la cadena de custody del caso.
        </p>
      </header>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-8 w-full animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs text-rose-700">
          {error ?? 'Error al cargar la integridad.'}
          <button
            type="button"
            onClick={() => void refetch()}
            className="ml-2 rounded border border-rose-200 bg-white px-2 py-0.5 text-[10px] font-semibold text-rose-700 hover:bg-rose-50"
          >
            Reintentar
          </button>
        </div>
      )}

      {integrity && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Estado
              </p>
              <StatusBadge value={integrity.status.toLowerCase()}>
                {integrity.status === 'VALID'
                  ? 'Válido'
                  : integrity.status === 'INVALID'
                    ? 'Inválido'
                    : integrity.status === 'PENDING'
                      ? 'Pendiente'
                      : 'Sin verificar'}
              </StatusBadge>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Algoritmo
              </p>
              <p className="font-mono text-xs text-slate-700">{integrity.algorithm}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Última verificación
              </p>
              <p className="text-xs text-slate-700">
                {integrity.last_verified_at
                  ? new Date(integrity.last_verified_at).toLocaleString('es-PE')
                  : '—'}
              </p>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50/60">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Campo
                  </th>
                  <th className="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Valor SHA-256
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(HASH_LABELS).map(([key, label]) => (
                  <tr key={key} className="border-b border-slate-100 last:border-0">
                    <td className="px-3 py-2 font-medium text-slate-700">{label}</td>
                    <td className="px-3 py-2">
                      <TruncatedHash
                        value={
                          integrity[key as keyof QualityQuarantineIntegrity] as string | null
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
