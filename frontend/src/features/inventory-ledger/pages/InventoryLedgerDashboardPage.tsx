import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { MetricCard } from '../../../components/common/MetricCard'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { InventoryLedgerPhaseNav } from '../components/InventoryLedgerPhaseNav'
import { InventoryLedgerContextEmptyState } from '../components/InventoryLedgerContextEmptyState'

interface InventoryMovementSummaryApi {
  id: string
  movement_code: string
  ledger_sequence: number
  movement_family: string
  movement_type: string
  status: string
  occurred_at: string
}

interface InventoryMovementListResponseApi {
  items: InventoryMovementSummaryApi[]
  total: number
  page: number
  page_size: number
}

export function InventoryLedgerDashboardPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext.organization_id

  const movements = useQuery<InventoryMovementListResponseApi>(
    ['inventory-ledger', 'dashboard', organizationId],
    '/logistics/inventory/movements',
    organizationId
      ? {
          organization_id: organizationId,
          page: 1,
          page_size: 10,
          sort_by: 'ledger_sequence',
          sort_direction: 'DESC',
        }
      : undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Libro de inventario" />
        <Alert variant="error">No tienes permisos para ver el libro de inventario.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044"
        title="Libro de inventario"
        description="Tablero técnico del kardex (libro de movimientos)."
        actions={
          <div className="flex gap-2">
            <Button onClick={() => navigate('/logistics/inventory/ledger/movements')}>
              Ver movimientos
            </Button>
            <Button variant="secondary" onClick={() => navigate('/logistics/inventory/ledger/kardex')}>
              Kardex técnico
            </Button>
          </div>
        }
      />

      <InventoryLedgerPhaseNav />

      <Alert variant="info">
        Este tablero presenta únicamente movimientos del libro técnico. No existe saldo definitivo editable en esta fase (Fase 045).
      </Alert>

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Activa el tablero del libro"
          description="Selecciona una organización para consultar sus movimientos recientes, particiones e integridad técnica."
        />
      )}

      {movements.isLoading && <LoadingSkeleton rows={6} />}

      {movements.isError && (
        <Alert variant="error">{getErrorMessage(movements.error)}</Alert>
      )}

      {organizationId && !movements.isLoading && !movements.isError && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <MetricCard
              label="Movimientos registrados"
              value={movements.data?.total ?? 0}
              detail="Libro append-only"
              icon="package"
            />
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700">
                <LogisticsIcon name="shield" size={21} aria-hidden="true" />
              </div>
              <h3 className="mt-4 text-sm font-semibold text-slate-900">Integridad y checkpoints</h3>
              <p className="mt-1 text-sm leading-6 text-slate-500">Verifica las particiones y crea checkpoints por rango.</p>
              <Button
                variant="secondary"
                size="small"
                className="mt-3"
                onClick={() => navigate('/logistics/inventory/ledger/checkpoints')}
              >
                Abrir checkpoints
              </Button>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                <LogisticsIcon name="layers" size={21} aria-hidden="true" />
              </div>
              <h3 className="mt-4 text-sm font-semibold text-slate-900">Particiones del libro</h3>
              <p className="mt-1 text-sm leading-6 text-slate-500">Consulta la secuencia y el último hash de cada partición.</p>
              <Button
                variant="secondary"
                size="small"
                className="mt-3"
                onClick={() => navigate('/logistics/inventory/ledger/partitions')}
              >
                Ver particiones
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-700">Movimientos recientes</h3>
            {movements.data?.items.length ? (
              <div className="space-y-1">
                {movements.data.items.map((movement) => (
                  <div
                    key={movement.id}
                    className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-300 cursor-pointer"
                    onClick={() => navigate(`/logistics/inventory/ledger/movements/${movement.id}`)}
                  >
                    <div>
                      <span className="font-medium">{movement.movement_code}</span>
                      <span className="ml-2 text-sm text-gray-500">{movement.movement_type}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">
                        {movement.status}
                      </span>
                      <span className="text-gray-500">#{movement.ledger_sequence}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 bg-white rounded-lg border">
                Sin movimientos registrados.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
