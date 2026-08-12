import type { PutawayTask } from '../types/putaway'

interface Props {
  task: PutawayTask
  onClick?: () => void
  isActive?: boolean
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-yellow-100 text-yellow-700',
  on_hold: 'bg-purple-100 text-purple-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  cancelled: 'bg-gray-100 text-gray-500',
}

export function TaskCard({ task, onClick, isActive }: Props) {
  return (
    <div
      className={`p-4 rounded-lg border cursor-pointer ${
        isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <span className="font-medium">{task.product.sku}</span>
          <span className="ml-2 text-sm text-gray-500">{task.product.name}</span>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${STATUS_COLORS[task.status]}`}>
          {task.status}
        </span>
      </div>
      <div className="mt-2 flex gap-4 text-sm text-gray-500">
        <span>{task.quantity.value} {task.unit.symbol}</span>
        {task.source_location && <span>Desde: {task.source_location.code}</span>}
        {task.destination_location && <span>Hacia: {task.destination_location.code}</span>}
      </div>
      {task.lot && <div className="text-xs text-gray-400 mt-1">Lote: {task.lot.lot_code}</div>}
      {task.assigned_user && (
        <div className="text-xs text-gray-400 mt-1">Asignado: {task.assigned_user.display_name}</div>
      )}
    </div>
  )
}
