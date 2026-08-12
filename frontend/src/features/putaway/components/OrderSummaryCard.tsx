import type { PutawayOrderSummary } from '../types/putaway'

interface Props {
  order: PutawayOrderSummary
  onClick?: () => void
}

const STATUS_LABELS: Record<string, string> = {
  draft: 'Borrador',
  planned: 'Planificada',
  in_progress: 'En progreso',
  partially_completed: 'Parcial',
  completed: 'Completada',
  cancelled: 'Cancelada',
  on_hold: 'En espera',
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  planned: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-yellow-100 text-yellow-700',
  partially_completed: 'bg-orange-100 text-orange-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
  on_hold: 'bg-purple-100 text-purple-700',
}

export function OrderSummaryCard({ order, onClick }: Props) {
  const progress = order.total_lines > 0 ? (order.completed_lines / order.total_lines) * 100 : 0

  return (
    <div
      className="p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">{order.order_number}</div>
          <div className="text-sm text-gray-500">{order.source_type} — {order.warehouse.name}</div>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${STATUS_COLORS[order.status]}`}>
          {STATUS_LABELS[order.status]}
        </span>
      </div>
      <div className="mt-3">
        <div className="flex items-center justify-between text-sm text-gray-500 mb-1">
          <span>Progreso</span>
          <span>{order.completed_lines}/{order.total_lines} líneas</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${progress}%` }} />
        </div>
      </div>
      {order.assigned_user && (
        <div className="mt-2 text-xs text-gray-400">
          Asignado: {order.assigned_user.display_name}
        </div>
      )}
      {order.due_at && (
        <div className="mt-1 text-xs text-gray-400">
          Vence: {new Date(order.due_at).toLocaleDateString()}
        </div>
      )}
    </div>
  )
}
