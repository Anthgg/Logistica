import { useState } from 'react'
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
import type { InventoryWarehouseBalance } from '../types/inventory-balances'

type Tab = 'productos' | 'ubicaciones' | 'zonas' | 'estados' | 'movimientos' | 'frescura' | 'reconciliacion'

export function InventoryWarehouseBalanceDetailPage() {
  const { warehouseId } = useParams<{ warehouseId: string }>()
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const [activeTab, setActiveTab] = useState<Tab>('productos')

  const warehouse = useQuery<InventoryWarehouseBalance>(
    ['inventory-balances', 'warehouse', warehouseId ?? ''],
    `/logistics/inventory/balances/warehouses/${warehouseId}`,
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(warehouseId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Detalle de almacén" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  if (warehouse.isLoading) return <LoadingSkeleton rows={8} />
  if (warehouse.isError) return <Alert variant="error">{getErrorMessage(warehouse.error)}</Alert>
  if (!warehouse.data) return <Alert variant="info">Almacén no encontrado.</Alert>

  const w = warehouse.data
  const tabs: { id: Tab; label: string }[] = [
    { id: 'productos', label: 'Productos' },
    { id: 'ubicaciones', label: 'Ubicaciones' },
    { id: 'zonas', label: 'Zonas' },
    { id: 'estados', label: 'Estados' },
    { id: 'movimientos', label: 'Movimientos' },
    { id: 'frescura', label: 'Frescura' },
    { id: 'reconciliacion', label: 'Reconciliación' },
  ]

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title={w.warehouse.name}
        description={`Código: ${w.warehouse.code} · ${w.product_count} productos · ${w.location_count} ubicaciones`}
        actions={
          <div className="flex gap-2">
            <Button onClick={() => navigate(`/logistics/inventory/ledger/movements?warehouse_id=${w.warehouse_id}`)}>
              Ver movimientos
            </Button>
            <Button variant="secondary" onClick={() => navigate(-1)}>Volver</Button>
          </div>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Productos con stock</div>
          <div className="text-lg font-bold text-ink">{w.product_count}</div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Disponibles</div>
          <div className="text-lg font-bold text-ink">{w.available_products}</div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Reservados</div>
          <div className="text-lg font-bold text-ink">{w.reserved_products}</div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Bloqueados</div>
          <div className="text-lg font-bold text-ink">{w.blocked_products}</div>
        </div>
      </div>

      <div className="flex gap-1 border-b border-[#DDE4E8]">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-primary text-primary'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'productos' && (
        <div className="text-xs text-muted space-y-1">
          <p>Cuarentena: {w.quarantine_products} productos</p>
          <p>Dañados: {w.damaged_products} productos</p>
          <p>Vencidos: {w.expired_products} productos</p>
          <p>Pendientes putaway: {w.pending_putaway_products} productos</p>
        </div>
      )}

      {activeTab === 'movimientos' && (
        <Button size="sm" onClick={() => navigate(`/logistics/inventory/ledger/movements?warehouse_id=${w.warehouse_id}`)}>
          Ver movimientos del almacén
        </Button>
      )}

      {activeTab === 'frescura' && (
        <div className="text-xs text-muted space-y-1">
          <p>Estado: {w.freshness_state}</p>
          <DataQualityBadge status={w.data_quality} />
        </div>
      )}
    </div>
  )
}
