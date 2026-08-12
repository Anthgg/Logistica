import type { PutawayOrder } from '../types/putaway'

interface Props {
  order: PutawayOrder
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

export function OrderDetailHeader({ order }: Props) {
  const progress = order.total_lines > 0 ? (order.completed_lines / order.total_lines) * 100 : 0

  return (
    <div className="bg-white p-4 rounded-lg border space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">{order.order_number}</h2>
          <div className="text-sm text-gray-500">{order.source_type} — {order.warehouse.name}</div>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">{STATUS_LABELS[order.status]}</div>
          <div className="text-sm text-gray-500">Prioridad: {order.priority}</div>
        </div>
      </div>
      <div>
        <div className="flex items-center justify-between text-sm text-gray-500 mb-1">
          <span>Progreso</span>
          <span>{order.completed_lines}/{order.total_lines} líneas ({Math.round(progress)}%)</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${progress}%` }} />
        </div>
      </div>
      {order.assigned_user && (
        <div className="text-sm text-gray-500">
          Asignado: {order.assigned_user.display_name}
        </div>
      )}
      {order.due_at && (
        <div className="text-sm text-gray-500">
          Vence: {new Date(order.due_at).toLocaleDateString()}
        </div>
      )}
    </div>
  )
}
