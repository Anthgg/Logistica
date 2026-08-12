import type { PutawayOrderLine } from '../types/putaway'

interface Props {
  lines: PutawayOrderLine[]
  onLineClick?: (line: PutawayOrderLine) => void
}

const LINE_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  in_transit: 'bg-yellow-100 text-yellow-700',
  placed: 'bg-green-100 text-green-700',
  confirmed: 'bg-blue-100 text-blue-700',
  diverted: 'bg-orange-100 text-orange-700',
  exception: 'bg-red-100 text-red-700',
}

export function OrderLineList({ lines, onLineClick }: Props) {
  if (lines.length === 0) {
    return <div className="text-sm text-gray-500 py-4">Sin líneas.</div>
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">Líneas ({lines.length})</h3>
      {lines.map((line) => (
        <div
          key={line.line_id}
          className="flex items-center justify-between p-3 bg-white rounded-lg border cursor-pointer hover:bg-gray-50"
          onClick={() => onLineClick?.(line)}
        >
          <div>
            <span className="font-medium">{line.product.sku}</span>
            <span className="ml-2 text-sm text-gray-500">{line.product.name}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span>{line.quantity.value} {line.unit.symbol}</span>
            <span className={`px-2 py-1 text-xs rounded-full ${LINE_STATUS_COLORS[line.status]}`}>
              {line.status}
            </span>
            {line.suggested_location && (
              <span className="text-gray-500">→ {line.suggested_location.code}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
