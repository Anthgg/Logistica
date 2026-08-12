import type { InventoryMovementLine } from '../types/inventory-ledger'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'

interface Props {
  lines: InventoryMovementLine[]
  loading: boolean
}

const STATE_LABEL: Record<string, string> = {
  AVAILABLE: 'Disponible',
  BLOCKED: 'Bloqueado',
  RESERVED: 'Reservado',
  IN_TRANSIT: 'En tránsito',
  QUARANTINED: 'Cuarentena',
  DAMAGED: 'Dañado',
  EXPIRED: 'Vencido',
  PENDING: 'Pendiente',
  APPROVED: 'Aprobado',
  REJECTED: 'Rechazado',
  RELEASED: 'Liberado',
  STABLE: 'Estable',
  ARRIVED: 'Arribado',
  INTACT: 'Íntegro',
  PARTIAL: 'Parcial',
  VALID: 'Vigente',
  EXPIRING_SOON: 'Por vencer',
  UNKNOWN: '—',
}

export function InventoryMovementLinesTable({ lines, loading }: Props) {
  if (loading) return <LoadingSkeleton rows={4} />

  if (lines.length === 0) {
    return (
      <div className="bg-white p-8 rounded-lg border text-center text-gray-500">
        Sin líneas para este movimiento.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
          <tr>
            <th className="px-3 py-2 text-left">Línea</th>
            <th className="px-3 py-2 text-left">Producto / SKU</th>
            <th className="px-3 py-2 text-right">Cantidad</th>
            <th className="px-3 py-2 text-left">Unidad</th>
            <th className="px-3 py-2 text-left">Base (display)</th>
            <th className="px-3 py-2 text-left">Dirección</th>
            <th className="px-3 py-2 text-left">Origen → Destino</th>
            <th className="px-3 py-2 text-left">Estados</th>
            <th className="px-3 py-2 text-left">Tracking</th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line) => (
            <tr key={line.line_id} className="border-t">
              <td className="px-3 py-2 text-gray-500">#{line.line_number}</td>
              <td className="px-3 py-2">
                <div className="font-medium">{line.product.sku}</div>
                <div className="text-xs text-gray-500">{line.product.name}</div>
              </td>
              <td className="px-3 py-2 text-right font-mono">{line.quantity.value}</td>
              <td className="px-3 py-2 text-gray-500">{line.unit.symbol}</td>
              <td className="px-3 py-2 text-xs text-gray-500 font-mono">
                {line.base_quantity_display.value} {line.base_unit.symbol}
              </td>
              <td className="px-3 py-2">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  line.direction === 'IN' ? 'bg-green-100 text-green-700' :
                  line.direction === 'OUT' ? 'bg-orange-100 text-orange-700' :
                  'bg-blue-100 text-blue-700'
                }`}>
                  {line.direction === 'IN' ? '↑' : line.direction === 'OUT' ? '↓' : '↔'} {line.direction}
                </span>
              </td>
              <td className="px-3 py-2 text-xs">
                <div>{line.origin_position.location?.code ?? line.origin_position.external_boundary ?? '—'}</div>
                <div className="text-gray-500">→ {line.destination_position.location?.code ?? line.destination_position.external_boundary ?? '—'}</div>
              </td>
              <td className="px-3 py-2 text-xs">
                <div>{STATE_LABEL[line.origin_availability]} → {STATE_LABEL[line.destination_availability]}</div>
                <div className="text-gray-500">{STATE_LABEL[line.origin_quality]} → {STATE_LABEL[line.destination_quality]}</div>
              </td>
              <td className="px-3 py-2 text-xs text-gray-500 font-mono">{line.tracking_reference ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
