import { useNavigate } from 'react-router-dom'
import { Button } from '../../../components/common/Button'
import type { InventoryPositionBalance } from '../types/inventory-balances'

export function DrillDownDrawer({
  balance,
  onClose,
}: {
  balance: InventoryPositionBalance
  onClose: () => void
}) {
  const navigate = useNavigate()

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} aria-hidden="true" />
      <aside className="relative w-full max-w-lg bg-white shadow-xl overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink">Detalle de posición</h2>
          <button
            onClick={onClose}
            className="text-muted hover:text-ink text-lg"
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>
        <div className="p-4 space-y-4 text-sm">
          <section>
            <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">Producto</h3>
            <p className="text-ink">{balance.product.name}</p>
            <p className="text-muted text-xs">SKU: {balance.product.sku}</p>
          </section>
          <section>
            <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">Ubicación</h3>
            <p className="text-ink">{balance.warehouse.name}</p>
            {balance.location && (
              <p className="text-muted text-xs">{balance.location.code} · {balance.location.zone ?? '—'}</p>
            )}
            <p className="text-muted text-xs">Posición: {balance.position_id_display}</p>
          </section>
          <section>
            <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">Cantidades</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>Físico: <span className="font-medium text-ink">{balance.physical.value}</span></div>
              <div>Disponible: <span className="font-medium text-ink">{balance.available.value}</span></div>
              <div>Reservado: <span className="font-medium text-ink">{balance.reserved.value}</span></div>
              <div>Bloqueado: <span className="font-medium text-ink">{balance.blocked.value}</span></div>
              <div>Cuarentena: <span className="font-medium text-ink">{balance.quarantine.value}</span></div>
              <div>Tránsito: <span className="font-medium text-ink">{balance.transit.value}</span></div>
              <div>Dañado: <span className="font-medium text-ink">{balance.damaged.value}</span></div>
              <div>Vencido: <span className="font-medium text-ink">{balance.expired.value}</span></div>
            </div>
          </section>
          <section>
            <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">Secuencia</h3>
            <p className="text-ink">MOV: {balance.ledger_sequence?.toLocaleString('es-PE') ?? '—'}</p>
            <p className="text-muted text-xs">Balance: {balance.balance_sequence?.toLocaleString('es-PE') ?? '—'}</p>
            <p className="text-muted text-xs">Lag: {balance.projection_lag_movements} movimientos</p>
          </section>
          <section>
            <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">Fórmula</h3>
            <p className="text-ink">Estado: {balance.availability_state}</p>
            <p className="text-muted text-xs">Calidad: {balance.quality_state}</p>
          </section>
          {balance.hash_partial && (
            <section>
              <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">Hash</h3>
              <code className="text-xs text-muted break-all">{balance.hash_partial}</code>
            </section>
          )}
          <div className="pt-2 border-t flex gap-2">
            <Button
              size="sm"
              onClick={() => navigate(`/logistics/inventory/ledger/movements?product_id=${balance.product_id}&warehouse_id=${balance.warehouse_id}`)}
            >
              Ver movimientos
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => navigate(`/logistics/inventory/stock/products/${balance.product_id}`)}
            >
              Ver producto
            </Button>
          </div>
        </div>
      </aside>
    </div>
  )
}
