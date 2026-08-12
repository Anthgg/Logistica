import type { LocationCapacity } from '../types/putaway'

interface Props {
  capacity: LocationCapacity
  showDetails?: boolean
}

export function CapacityBar({ capacity, showDetails }: Props) {
  const utilization = parseFloat(capacity.utilization_percentage.value) || 0
  const color = utilization >= 90 ? 'bg-red-500' : utilization >= 70 ? 'bg-yellow-500' : 'bg-green-500'

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{capacity.location.code}</span>
        <span>{capacity.utilization_percentage.value}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${Math.min(utilization, 100)}%` }} />
      </div>
      {showDetails && (
        <div className="flex gap-4 text-xs text-gray-500">
          <span>Usado: {capacity.used_capacity.value} / {capacity.total_capacity.value} {capacity.unit.symbol}</span>
          {capacity.weight_capacity_kg && (
            <span>Peso: {capacity.weight_used_kg?.value ?? '0'} / {capacity.weight_capacity_kg.value} kg</span>
          )}
          {capacity.pallet_positions !== null && (
            <span>Posiciones: {capacity.pallet_positions_used ?? 0} / {capacity.pallet_positions}</span>
          )}
        </div>
      )}
    </div>
  )
}
