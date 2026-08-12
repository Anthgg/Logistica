import { useEffect, useState } from 'react'
import { costCentersApi } from '../../api/cost-centers-api'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type { CostCenter, PurchaseRequisitionPriority } from '../../types/purchase-requisitions'

interface CostCenterProps {
  value: string
  onChange: (id: string, name: string) => void
  disabled?: boolean
}

export function CostCenterSelector({ value, onChange, disabled = false }: CostCenterProps) {
  const [centers, setCenters] = useState<CostCenter[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    costCentersApi.list({ status: 'ACTIVE', limit: 100 })
      .then(setCenters)
      .catch(() => setCenters([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <label className="mb-1 block font-bold text-slate-700 text-xs">Centro de Costo Imputable *</label>
      <select
        value={value}
        onChange={(e) => {
          const selected = centers.find((c) => c.id === e.target.value)
          onChange(e.target.value, selected?.name || '')
        }}
        required
        disabled={disabled || loading}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white font-medium text-slate-800 focus:border-indigo-500 focus:outline-none"
      >
        <option value="">Seleccionar centro de costo...</option>
        {centers.map((c) => (
          <option key={c.id} value={c.id}>
            [{c.code}] {c.name}
          </option>
        ))}
      </select>
    </div>
  )
}

interface PriorityProps {
  priority: PurchaseRequisitionPriority
  priorityReason?: string
  onChange: (priority: PurchaseRequisitionPriority, reason?: string) => void
  disabled?: boolean
}

const PRIORITIES: { value: PurchaseRequisitionPriority; label: string; desc: string }[] = [
  { value: 'LOW', label: 'Baja', desc: 'Requerimientos de stock preventivo sin urgencia operativa.' },
  { value: 'NORMAL', label: 'Normal', desc: 'Requerimiento regular de reposición estándar.' },
  { value: 'HIGH', label: 'Alta', desc: 'Requerimiento prioritario para operación cercana.' },
  { value: 'URGENT', label: 'Urgente', desc: 'Riesgo inminente de parada de línea u operación.' },
  { value: 'CRITICAL', label: 'Crítica', desc: 'Parada de planta u operación en curso.' },
]

export function RequisitionPrioritySelector({
  priority,
  priorityReason = '',
  onChange,
  disabled = false,
}: PriorityProps) {
  const isHighPriority = priority === 'URGENT' || priority === 'CRITICAL'

  return (
    <div className="space-y-3 text-xs">
      <div>
        <label className="mb-1 block font-bold text-slate-700">Prioridad Operativa *</label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {PRIORITIES.map((p) => (
            <button
              key={p.value}
              type="button"
              disabled={disabled}
              onClick={() => onChange(p.value, priorityReason)}
              className={`rounded-xl border p-2.5 text-center transition-colors ${
                priority === p.value
                  ? 'border-indigo-600 bg-indigo-50/80 font-bold text-indigo-950 shadow-xs'
                  : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
              }`}
            >
              <span className="block text-xs font-bold">{p.label}</span>
            </button>
          ))}
        </div>
      </div>

      {isHighPriority && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-3.5 space-y-2">
          <p className="text-amber-900 text-[11px] flex items-start gap-1.5">
            <LogisticsIcon name="alert" size={14} aria-hidden /> <span><strong>Justificación Adicional Requerida:</strong> La prioridad urgente/crítica requiere motivo explícito y ejecución de Step-Up Auth al enviar. No garantiza compra inmediata ni omite la revisión de aprobación.</span>
          </p>
          <textarea
            value={priorityReason}
            onChange={(e) => onChange(priority, e.target.value)}
            rows={2}
            required
            disabled={disabled}
            placeholder="Explica la urgencia o riesgo de parada de planta..."
            className="w-full resize-none rounded-lg border border-amber-300 bg-white px-3 py-2 text-xs"
          />
        </div>
      )}
    </div>
  )
}
