import { useParams, useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { Button } from '../../../components/common/Button'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { getErrorMessage } from '../../../utils/errors'
import { DecimalDisplay } from '../components/DecimalDisplay'
import { DataQualityBadge } from '../components/DataQualityBadge'
import type { InventoryLocationBalance } from '../types/inventory-balances'

export function InventoryLocationBalanceDetailPage() {
  const { locationId } = useParams<{ locationId: string }>()
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const location = useQuery<InventoryLocationBalance>(
    ['inventory-balances', 'location', locationId ?? ''],
    `/logistics/inventory/balances/locations/${locationId}`,
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(locationId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Detalle de ubicación" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  if (location.isLoading) return <LoadingSkeleton rows={8} />
  if (location.isError) return <Alert variant="error">{getErrorMessage(location.error)}</Alert>
  if (!location.data) return <Alert variant="info">Ubicación no encontrada.</Alert>

  const l = location.data

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title={l.location.code}
        description={`${l.warehouse.name} · ${l.location.zone ?? 'Sin zona'} · ${l.location.aisl ?? '—'}-${l.location.rack ?? '—'}-${l.location.level ?? '—'}-${l.location.position ?? '—'}`}
        actions={
          <div className="flex gap-2">
            <Button onClick={() => navigate(`/logistics/inventory/ledger/movements?location_id=${l.location_id}`)}>
              Ver movimientos
            </Button>
            <Button variant="secondary" onClick={() => navigate(-1)}>Volver</Button>
          </div>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Físico</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={l.physical} /></div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Disponible</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={l.available} /></div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Reservado</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={l.reserved} /></div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Bloqueado</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={l.blocked} /></div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Cuarentena</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={l.quarantine} /></div>
        </div>
      </div>

      <div className="text-xs text-muted space-y-1">
        <p>Producto: <span className="font-medium text-ink">{l.product.name}</span> ({l.product.sku})</p>
        <p>Unidad: {l.unit.code}</p>
        <p>Estado disponibilidad: {l.availability_state}</p>
        <p>Estado calidad: {l.quality_state}</p>
        <p>Frescura: {l.freshness_state}</p>
        <p>Último MOV: {l.latest_movement?.movement_code ?? '—'}</p>
        <DataQualityBadge status={l.data_quality} />
      </div>
    </div>
  )
}
