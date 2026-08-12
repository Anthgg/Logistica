import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { PutawayPreparation } from '../types/quarantine'

function ReadOnlyField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex flex-col">
      <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className="text-sm text-slate-800">{value ?? '—'}</dd>
    </div>
  )
}

function HashValue({ value }: { value: string | null }) {
  if (!value) return <span className="text-slate-400">—</span>
  const truncated = value.length > 20 ? `${value.slice(0, 10)}…${value.slice(-10)}` : value
  return (
    <span className="font-mono text-[11px] text-slate-700" title={value}>
      {truncated}
    </span>
  )
}

export function PutawayPreparationPanel({
  allocationId,
}: {
  allocationId: string
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.quarantine.viewPutawayPreparation)

  const {
    data: preparation,
    isLoading,
    isError,
    error,
  } = useQuery<PutawayPreparation>(
    ['putaway-preparation', allocationId],
    `/logistics/quality-availability/putaway-preparation/${allocationId}`,
    undefined,
    { enabled: canView },
  )

  if (!canView) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-800">Preparación de putaway</h2>
        <p className="mt-2 text-xs text-slate-500">No tiene permisos para ver esta información.</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
      <header className="mb-3 border-b border-slate-100 pb-2">
        <h2 className="text-sm font-bold text-slate-800">Preparación de putaway</h2>
        <p className="mt-0.5 text-xs text-slate-500">
          Disponibilidad liberada para generación de orden de putaway en Fase 043.
        </p>
      </header>

      <div className="mb-3 rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-[11px] text-amber-700">
        Disponible para generar una orden de putaway en Fase 043. No se crea tarea PUT ni se
        selecciona ubicación final.
      </div>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-10 w-full animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs text-rose-700">
          {error ?? 'Error al cargar la preparación de putaway.'}
        </div>
      )}

      {preparation && (
        <div className="space-y-4">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-2 text-xs sm:grid-cols-2">
            <ReadOnlyField
              label="Asignación liberada"
              value={preparation.release_authorization_id}
            />
            <ReadOnlyField label="Producto" value={preparation.product?.name ?? null} />
            <ReadOnlyField label="Cantidad" value={preparation.quantity} />
            <ReadOnlyField label="Unidad" value={preparation.unit?.symbol ?? null} />
            <ReadOnlyField
              label="Restricciones"
              value={
                preparation.status === 'PENDING'
                  ? 'Ninguna'
                  : preparation.status
              }
            />
            <ReadOnlyField
              label="Temperatura"
              value={preparation.product?.temperature_declared ?? null}
            />
          </dl>

          <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
            <h3 className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              Lotes observados
            </h3>
            <p className="text-xs text-slate-700">
              {preparation.lot_number ?? 'Sin lote registrado'}
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
            <h3 className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              Seriales observados
            </h3>
            <p className="text-xs text-slate-700">
              {preparation.serial_number ?? 'Sin serial registrado'}
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 text-xs sm:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
              <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Expiraciones
              </h3>
              <p className="text-slate-700">—</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
              <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Calidad
              </h3>
              <p className="text-slate-700">Liberada</p>
            </div>
          </div>

          <dl className="grid grid-cols-1 gap-x-4 gap-y-2 text-xs sm:grid-cols-2">
            <div className="flex flex-col">
              <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Hash de liberación
              </dt>
              <dd>
                <HashValue value={null} />
              </dd>
            </div>
            <ReadOnlyField label="Bloqueos" value="Ninguno" />
            <ReadOnlyField
              label="Elegibilidad"
              value="Disponible para putaway"
            />
          </dl>
        </div>
      )}
    </div>
  )
}
