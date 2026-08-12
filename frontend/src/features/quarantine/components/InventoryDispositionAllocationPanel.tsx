import type { InboundInventoryDispositionAllocation, InventoryDispositionSplit } from '../types/quarantine'
import { StatusBadge } from '../../../components/common/StatusBadge'

interface Props {
  allocation: InboundInventoryDispositionAllocation
  split: InventoryDispositionSplit | null
}

export function InventoryDispositionAllocationPanel({ allocation, split }: Props) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-ink mb-3">Asignación de disposición de inventario</h3>
        <div className="rounded-lg border border-slate-200 divide-y divide-slate-200">
          {/* Original Quantity */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Cantidad original</span>
              <p className="font-medium text-ink">{allocation.expected_quantity} {allocation.unit.symbol}</p>
            </div>
            <div>
              <span className="text-muted">Cantidad actual</span>
              <p className="font-medium text-ink">{allocation.allocated_quantity} {allocation.unit.symbol}</p>
            </div>
          </div>

          {/* Unit & Status */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Unidad de medida</span>
              <p className="font-medium text-ink">{allocation.unit.name} ({allocation.unit.symbol})</p>
            </div>
            <div>
              <span className="text-muted">Estado de disposición</span>
              <div className="mt-1">
                <StatusBadge value={allocation.disposition_status} />
              </div>
            </div>
          </div>

          {/* Availability & Quality */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Clase de disponibilidad</span>
              <div className="mt-1">
                <StatusBadge value={allocation.availability_class} />
              </div>
            </div>
            <div>
              <span className="text-muted">Estado de calidad</span>
              <div className="mt-1">
                <StatusBadge value={allocation.quality_status} />
              </div>
            </div>
          </div>

          {/* Parent Allocation */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Asignación padre</span>
              <p className="font-medium text-ink">{allocation.reinspection_of_allocation_id ?? 'N/A'}</p>
            </div>
            <div>
              <span className="text-muted">Reinspección</span>
              <p className="font-medium text-ink">{allocation.is_reinspection ? 'Sí' : 'No'}</p>
            </div>
          </div>

          {/* Quantity Breakdown */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Cantidad liberada</span>
              <p className="font-medium text-emerald-600">{allocation.released_quantity} {allocation.unit.symbol}</p>
            </div>
            <div>
              <span className="text-muted">Cantidad rechazada</span>
              <p className="font-medium text-rose-600">{allocation.rejected_quantity} {allocation.unit.symbol}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Cantidad aún bloqueada</span>
              <p className="font-medium text-amber-600">{allocation.quarantined_quantity} {allocation.unit.symbol}</p>
            </div>
            <div>
              <span className="text-muted">ID de asignación</span>
              <p className="font-medium text-ink text-[11px] font-mono">{allocation.allocation_id}</p>
            </div>
          </div>

          {/* Divisions (if split exists) */}
          {split && (
            <div className="p-4 text-xs">
              <span className="text-muted">Historial de divisiones</span>
              <div className="mt-2 rounded border border-slate-200 divide-y divide-slate-200">
                <div className="grid grid-cols-4 gap-2 p-2 bg-slate-50 text-[10px] font-semibold text-muted">
                  <span>Tipo</span>
                  <span>Cantidad</span>
                  <span>Destino</span>
                  <span>Fecha</span>
                </div>
                {split.split_history.map((record) => (
                  <div key={record.split_id} className="grid grid-cols-4 gap-2 p-2 text-[11px]">
                    <StatusBadge value={record.split_type} />
                    <span className="text-ink">{record.quantity} {allocation.unit.symbol}</span>
                    <span className="text-muted">{record.destination ?? 'N/A'}</span>
                    <span className="text-muted">{new Date(record.created_at).toLocaleDateString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
