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
import type { InventoryPositionBalance } from '../types/inventory-balances'

export function InventoryPositionBalanceDetailPage() {
  const { positionId } = useParams<{ positionId: string }>()
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const position = useQuery<InventoryPositionBalance>(
    ['inventory-balances', 'position', positionId ?? ''],
    `/logistics/inventory/balances/positions/${positionId}`,
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(positionId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Detalle de posición" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  if (position.isLoading) return <LoadingSkeleton rows={8} />
  if (position.isError) return <Alert variant="error">{getErrorMessage(position.error)}</Alert>
  if (!position.data) return <Alert variant="info">Posición no encontrada.</Alert>

  const p = position.data

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title={`Posición ${p.position_id_display}`}
        description={`${p.product.name} · ${p.warehouse.name}`}
        actions={
          <div className="flex gap-2">
            <Button onClick={() => navigate(`/logistics/inventory/ledger/movements?position_id=${p.position_id}`)}>
              Ver movimientos
            </Button>
            <Button variant="secondary" onClick={() => navigate(-1)}>Volver</Button>
          </div>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Físico', value: p.physical },
          { label: 'Disponible', value: p.available },
          { label: 'Reservado', value: p.reserved },
          { label: 'Bloqueado', value: p.blocked },
          { label: 'Cuarentena', value: p.quarantine },
        ].map((item) => (
          <div key={item.label} className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
            <div className="text-[10px] text-muted uppercase tracking-wide">{item.label}</div>
            <div className="text-lg font-bold text-ink"><DecimalDisplay value={item.value} /></div>
            <div className="text-[10px] text-muted">{p.unit.code}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {[
          { label: 'Tránsito', value: p.transit },
          { label: 'Dañado', value: p.damaged },
          { label: 'Vencido', value: p.expired },
          { label: 'Pendiente putaway', value: p.pending_putaway },
          { label: 'Rechazado', value: p.rejected },
        ].map((item) => (
          <div key={item.label} className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
            <div className="text-[10px] text-muted uppercase tracking-wide">{item.label}</div>
            <div className="text-lg font-bold text-ink"><DecimalDisplay value={item.value} /></div>
          </div>
        ))}
      </div>

      <div className="space-y-3 text-xs">
        <section className="bg-white border border-[#DDE4E8] rounded-[10px] p-4">
          <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Identidad</h3>
          <div className="grid grid-cols-2 gap-2">
            <div>Position ID: <span className="font-medium text-ink font-mono">{p.position_id}</span></div>
            <div>Key parcial: <span className="font-mono text-muted">{p.dimension_key_partial}</span></div>
            <div>Producto: <span className="font-medium text-ink">{p.product.name}</span></div>
            <div>SKU: <span className="text-ink">{p.product.sku}</span></div>
            <div>Almacén: <span className="font-medium text-ink">{p.warehouse.name}</span></div>
            <div>Ubicación: <span className="text-ink">{p.location?.code ?? '—'}</span></div>
          </div>
        </section>

        <section className="bg-white border border-[#DDE4E8] rounded-[10px] p-4">
          <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Secuencia e integridad</h3>
          <div className="grid grid-cols-2 gap-2">
            <div>Secuencia MOV: <span className="font-medium text-ink">{p.ledger_sequence?.toLocaleString('es-PE') ?? '—'}</span></div>
            <div>Secuencia balance: <span className="font-medium text-ink">{p.balance_sequence?.toLocaleString('es-PE') ?? '—'}</span></div>
            <div>Lag: <span className="text-ink">{p.projection_lag_movements} movimientos</span></div>
            <div>Hash: <span className="font-mono text-muted break-all">{p.hash_partial ?? '—'}</span></div>
          </div>
        </section>

        <section className="bg-white border border-[#DDE4E8] rounded-[10px] p-4">
          <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Estados</h3>
          <div className="grid grid-cols-2 gap-2">
            <div>Disponibilidad: <span className="text-ink">{p.availability_state}</span></div>
            <div>Calidad: <span className="text-ink">{p.quality_state}</span></div>
            <div>Tránsito: <span className="text-ink">{p.transit_state}</span></div>
            <div>Daño: <span className="text-ink">{p.damage_state}</span></div>
            <div>Vencimiento: <span className="text-ink">{p.expiration_state}</span></div>
            <div>Propiedad: <span className="text-ink">{p.ownership ?? '—'}</span></div>
          </div>
          <div className="mt-2"><DataQualityBadge status={p.data_quality} /></div>
        </section>

        <section className="bg-white border border-[#DDE4E8] rounded-[10px] p-4">
          <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Reconciliación</h3>
          <p>Estado: {p.reconciliation_status ?? '—'}</p>
          {p.tracking_reference_partial && (
            <p className="mt-1">Tracking: <span className="font-mono text-muted">{p.tracking_reference_partial}</span></p>
          )}
        </section>

        {p.last_movement && (
          <section className="bg-white border border-[#DDE4E8] rounded-[10px] p-4">
            <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Último movimiento</h3>
            <div className="grid grid-cols-2 gap-2">
              <div>Código: <span className="font-medium text-ink">{p.last_movement.movement_code}</span></div>
              <div>Tipo: <span className="text-ink">{p.last_movement.movement_type}</span></div>
              <div>Fecha: <span className="text-ink">{new Date(p.last_movement.occurred_at).toLocaleString('es-PE')}</span></div>
              <div>Secuencia: <span className="text-ink">{p.last_movement.ledger_sequence}</span></div>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
