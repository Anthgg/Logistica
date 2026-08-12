import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import type { PutawayStrategy, PutawayPlanParameters } from '../types/putaway'

interface Props {
  onPlan: (strategy: PutawayStrategy, parameters: PutawayPlanParameters) => void
  isPending?: boolean
}

export function PlanningWizard({ onPlan, isPending }: Props) {
  const [strategy, setStrategy] = useState<PutawayStrategy>('auto_optimal')
  const [parameters, setParameters] = useState<PutawayPlanParameters>({
    prefer_closest: true,
    respect_rotation: true,
    max_distance_meters: 500,
    preferred_zones: [],
    excluded_zones: [],
    allow_split: true,
    max_locations_per_line: 3,
    temperature_enforcement: 'strict',
    hazmat_enforcement: 'strict',
  })

  return (
    <div className="bg-white p-6 rounded-lg border space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Estrategia de planificación</label>
        <select
          value={strategy}
          onChange={(e) => setStrategy(e.target.value as PutawayStrategy)}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="auto_optimal">Óptima automática</option>
          <option value="capacity_first">Capacidad primero</option>
          <option value="proximity_first">Proximidad primero</option>
          <option value="rotation_first">Rotación primero</option>
          <option value="manual">Manual</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={parameters.prefer_closest}
            onChange={(e) => setParameters((p) => ({ ...p, prefer_closest: e.target.checked }))}
            className="rounded"
          />
          <span className="text-sm">Más cercana</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={parameters.respect_rotation}
            onChange={(e) => setParameters((p) => ({ ...p, respect_rotation: e.target.checked }))}
            className="rounded"
          />
          <span className="text-sm">Respetar rotación</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={parameters.allow_split}
            onChange={(e) => setParameters((p) => ({ ...p, allow_split: e.target.checked }))}
            className="rounded"
          />
          <span className="text-sm">Permitir división</span>
        </label>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Distancia máx (m)</label>
          <input
            type="number"
            value={parameters.max_distance_meters ?? 500}
            onChange={(e) => setParameters((p) => ({ ...p, max_distance_meters: Number(e.target.value) }))}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Máx ubicaciones/línea</label>
          <input
            type="number"
            value={parameters.max_locations_per_line}
            onChange={(e) => setParameters((p) => ({ ...p, max_locations_per_line: Number(e.target.value) }))}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>
      </div>

      <div className="flex gap-2 justify-end">
        <Button onClick={() => onPlan(strategy, parameters)} disabled={isPending}>
          {isPending ? 'Planificando...' : 'Planificar'}
        </Button>
      </div>
    </div>
  )
}
