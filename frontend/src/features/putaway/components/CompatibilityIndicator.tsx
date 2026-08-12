import type { ProductLocationCompatibility } from '../types/putaway'

interface Props {
  compatibility: ProductLocationCompatibility
}

export function CompatibilityIndicator({ compatibility }: Props) {
  const isCompatible = compatibility.is_compatible
  const hasIncompatibilities = compatibility.incompatibilities.length > 0

  return (
    <div className={`p-3 rounded-lg border ${
      isCompatible ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
    }`}>
      <div className="flex items-center gap-2">
        <span className={`text-lg ${isCompatible ? 'text-green-600' : 'text-red-600'}`}>
          {isCompatible ? '✓' : '✗'}
        </span>
        <span className="font-medium">
          {isCompatible ? 'Compatible' : 'Incompatible'}
        </span>
      </div>
      <div className="mt-2 flex gap-3 text-sm">
        <span className={compatibility.temperature_compatible ? 'text-green-600' : 'text-red-600'}>
          {compatibility.temperature_compatible ? '✓' : '✗'} Temperatura
        </span>
        <span className={compatibility.hazmat_compatible ? 'text-green-600' : 'text-red-600'}>
          {compatibility.hazmat_compatible ? '✓' : '✗'} Hazmat
        </span>
        <span className={compatibility.category_allowed ? 'text-green-600' : 'text-red-600'}>
          {compatibility.category_allowed ? '✓' : '✗'} Categoría
        </span>
      </div>
      {hasIncompatibilities && (
        <div className="mt-2 space-y-1">
          {compatibility.incompatibilities.map((inc) => (
            <div key={inc.rule_id} className="text-xs text-red-600">
              [{inc.severity}] {inc.reason}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
