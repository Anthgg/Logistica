import type { ProximityDestination } from '../types/putaway'

interface Props {
  destinations: ProximityDestination[]
}

export function ProximityList({ destinations }: Props) {
  if (destinations.length === 0) {
    return <div className="text-sm text-gray-500 py-4">Sin destinos cercanos.</div>
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">Destinos cercanos ({destinations.length})</h3>
      {destinations.map((d) => (
        <div key={d.location_id} className={`p-3 rounded-lg border ${
          d.is_preferred ? 'border-blue-300 bg-blue-50' : 'border-gray-200'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium">{d.location.code}</span>
              <span className="ml-2 text-sm text-gray-500">{d.location.name}</span>
              {d.is_preferred && <span className="ml-2 text-xs bg-blue-100 px-2 py-0.5 rounded-full text-blue-700">Preferido</span>}
            </div>
            <div className="text-sm text-gray-500">
              {d.distance_meters.value}m — {d.walk_time_seconds}s
            </div>
          </div>
          {d.zone_match && <div className="text-xs text-green-600 mt-1">✓ Misma zona</div>}
        </div>
      ))}
    </div>
  )
}
