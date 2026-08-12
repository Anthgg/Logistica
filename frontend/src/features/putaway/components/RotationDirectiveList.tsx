import type { RotationDirective } from '../types/putaway'

interface Props {
  directives: RotationDirective[]
}

export function RotationDirectiveList({ directives }: Props) {
  if (directives.length === 0) {
    return <div className="text-sm text-gray-500 py-4">Sin directivas de rotación.</div>
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">Directivas de rotación</h3>
      {directives.map((d) => (
        <div key={d.directive_id} className="p-3 bg-white rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium">{d.product.sku}</span>
              <span className="ml-2 text-sm text-gray-500">{d.product.name}</span>
            </div>
            <span className={`px-2 py-1 text-xs rounded-full ${
              d.method === 'FIFO' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
            }`}>
              {d.method}
            </span>
          </div>
          <div className="mt-2 flex gap-4 text-sm text-gray-500">
            <span>Cantidad: {d.quantity_available.value}</span>
            {d.oldest_days_in_stock !== null && (
              <span>{d.oldest_days_in_stock} días en stock</span>
            )}
            {d.is_expired && <span className="text-red-600">Vencido</span>}
            {d.is_expiring_soon && <span className="text-yellow-600">Por vencer</span>}
          </div>
          {d.expiration_date && (
            <div className="text-xs text-gray-400 mt-1">
              Vence: {new Date(d.expiration_date).toLocaleDateString()}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
