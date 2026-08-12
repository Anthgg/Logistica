import type { LocationCandidate } from '../types/putaway'

interface Props {
  candidates: LocationCandidate[]
  onSelect?: (candidate: LocationCandidate) => void
  selectedLocationId?: string
}

export function LocationCandidatesList({ candidates, onSelect, selectedLocationId }: Props) {
  if (candidates.length === 0) {
    return <div className="text-sm text-gray-500 py-4">No hay candidatos disponibles.</div>
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">Candidatos de ubicación ({candidates.length})</h3>
      {candidates.map((candidate) => (
        <div
          key={candidate.location_id}
          className={`p-4 rounded-lg border cursor-pointer ${
            selectedLocationId === candidate.location_id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-blue-300'
          }`}
          onClick={() => onSelect?.(candidate)}
        >
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium">{candidate.location.code}</span>
              <span className="ml-2 text-sm text-gray-500">{candidate.location.name}</span>
              <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded-full">#{candidate.rank}</span>
            </div>
            <span className="font-medium text-blue-600">Score: {candidate.score.value}</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {candidate.reasons.map((reason) => (
              <span key={reason} className="text-xs bg-gray-100 px-2 py-0.5 rounded-full text-gray-600">
                {reason}
              </span>
            ))}
          </div>
          <div className="mt-2 flex gap-4 text-sm text-gray-500">
            <span>Capacidad: {candidate.capacity_percentage.value}%</span>
            {candidate.distance_from_source && (
              <span>Distancia: {candidate.distance_from_source.value}m</span>
            )}
            {candidate.temperature_match && <span className="text-green-600">✓ Temp</span>}
            {candidate.hazmat_compatible && <span className="text-green-600">✓ Hazmat</span>}
            {candidate.lot_grouping_match && <span className="text-green-600">✓ Lote</span>}
          </div>
          {candidate.warnings.length > 0 && (
            <div className="mt-2">
              {candidate.warnings.map((warning, i) => (
                <div key={i} className="text-xs text-yellow-600">⚠ {warning}</div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
