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
import type { InventoryProductBalance } from '../types/inventory-balances'

type Tab = 'resumen' | 'almacenes' | 'ubicaciones' | 'estados' | 'movimientos' | 'formulas'

export function InventoryProductBalanceDetailPage() {
  const { productId } = useParams<{ productId: string }>()
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const [activeTab, setActiveTab] = useState<Tab>('resumen')

  const product = useQuery<InventoryProductBalance>(
    ['inventory-balances', 'product', productId ?? ''],
    `/logistics/inventory/balances/products/${productId}`,
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(productId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Detalle de producto" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  if (product.isLoading) return <LoadingSkeleton rows={8} />
  if (product.isError) return <Alert variant="error">{getErrorMessage(product.error)}</Alert>
  if (!product.data) return <Alert variant="info">Producto no encontrado.</Alert>

  const p = product.data
  const tabs: { id: Tab; label: string }[] = [
    { id: 'resumen', label: 'Resumen' },
    { id: 'almacenes', label: 'Almacenes' },
    { id: 'ubicaciones', label: 'Ubicaciones' },
    { id: 'estados', label: 'Estados' },
    { id: 'movimientos', label: 'Movimientos' },
    { id: 'formulas', label: 'Fórmulas' },
  ]

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title={p.product.name}
        description={`SKU: ${p.product.sku} · ${p.unit.code}`}
        actions={
          <div className="flex gap-2">
            <Button onClick={() => navigate(`/logistics/inventory/ledger/movements?product_id=${p.product_id}`)}>
              Ver movimientos
            </Button>
            <Button variant="secondary" onClick={() => navigate(-1)}>
              Volver
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Físico</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={p.physical} /></div>
          <div className="text-[10px] text-muted">{p.unit.code}</div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Disponible</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={p.available} /></div>
          <div className="text-[10px] text-muted">{p.unit.code}</div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Reservado</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={p.reserved} /></div>
          <div className="text-[10px] text-muted">{p.unit.code}</div>
        </div>
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-3">
          <div className="text-[10px] text-muted uppercase tracking-wide">Bloqueado</div>
          <div className="text-lg font-bold text-ink"><DecimalDisplay value={p.blocked} /></div>
          <div className="text-[10px] text-muted">{p.unit.code}</div>
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

      {activeTab === 'resumen' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
            <div>Cuarentena: <DecimalDisplay value={p.quarantine} className="font-medium text-ink" /></div>
            <div>Tránsito: <DecimalDisplay value={p.transit} className="font-medium text-ink" /></div>
            <div>Dañado: <DecimalDisplay value={p.damaged} className="font-medium text-ink" /></div>
            <div>Vencido: <DecimalDisplay value={p.expired} className="font-medium text-ink" /></div>
            <div>Pendiente putaway: <DecimalDisplay value={p.pending_putaway} className="font-medium text-ink" /></div>
          </div>
          <div className="flex gap-4 text-xs text-muted">
            <span>Almacenes: {p.warehouse_count}</span>
            <span>Ubicaciones: {p.location_count}</span>
            <span>Posiciones: {p.position_count}</span>
            <DataQualityBadge status={p.data_quality} />
          </div>
        </div>
      )}

      {activeTab === 'almacenes' && (
        <div className="text-xs text-muted">
          {p.warehouses.map((w) => (
            <div key={w.warehouse_id} className="py-2 border-b border-[#EEF1F4]">
              <span className="font-medium text-ink">{w.name}</span> ({w.code})
            </div>
          ))}
          {p.warehouses.length === 0 && <p>No hay almacenes con saldo para este producto.</p>}
        </div>
      )}

      {activeTab === 'movimientos' && (
        <div className="text-xs text-muted">
          <Button size="sm" onClick={() => navigate(`/logistics/inventory/ledger/movements?product_id=${p.product_id}`)}>
            Ver movimientos del libro
          </Button>
        </div>
      )}

      {activeTab === 'formulas' && (
        <div className="text-xs text-muted">
          <p>Secuencia de balance: {p.balance_sequence?.toLocaleString('es-PE') ?? '—'}</p>
          <p>Frescura: {p.freshness_state}</p>
        </div>
      )}
    </div>
  )
}
