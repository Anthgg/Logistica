import type { PutawayException } from '../types/putaway'

interface Props {
  exception: PutawayException
  onAction?: (action: string) => void
}

const SEVERITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const TYPE_LABELS: Record<string, string> = {
  capacity_exceeded: 'Capacidad excedida',
  incompatible_product: 'Producto incompatible',
  rotation_violation: 'Violación de rotación',
  location_unavailable: 'Ubicación no disponible',
  scan_mismatch: 'Escaneo no coincide',
  lot_mismatch: 'Lote no coincide',
  serial_mismatch: 'Serie no coincide',
  temperature_violation: 'Violación de temperatura',
  hazmat_violation: 'Violación de hazardous',
  manual_override: 'Override manual',
}

export function ExceptionCard({ exception, onAction }: Props) {
  return (
    <div className={`p-4 rounded-lg border ${
      exception.severity === 'critical' ? 'border-red-300 bg-red-50' :
      exception.severity === 'high' ? 'border-orange-300 bg-orange-50' :
      'border-gray-200 bg-white'
    }`}>
      <div className="flex items-center justify-between">
        <div>
          <span className="font-medium">{TYPE_LABELS[exception.exception_type] ?? exception.exception_type}</span>
          <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${SEVERITY_COLORS[exception.severity]}`}>
            {exception.severity}
          </span>
        </div>
        <span className="text-sm text-gray-500">{exception.status}</span>
      </div>
      <div className="mt-1 text-sm text-gray-600">{exception.title}</div>
      <div className="mt-1 text-xs text-gray-500">{exception.description}</div>
      {exception.suggested_action && (
        <div className="mt-2 text-xs text-blue-600">Sugerencia: {exception.suggested_action}</div>
      )}
      {exception.status === 'open' && onAction && (
        <div className="mt-3 flex gap-2">
          <button className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded" onClick={() => onAction('acknowledge')}>
            Reconocer
          </button>
          <button className="text-xs px-3 py-1 bg-green-100 text-green-700 rounded" onClick={() => onAction('resolve')}>
            Resolver
          </button>
          <button className="text-xs px-3 py-1 bg-yellow-100 text-yellow-700 rounded" onClick={() => onAction('escalate')}>
            Escalar
          </button>
        </div>
      )}
    </div>
  )
}
