import { useState } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type { VehicleVerificationConflict, VehicleVerificationConflictResolve } from '../../types/vehicle-verifications'

interface PanelProps {
  conflicts: VehicleVerificationConflict[]
  onResolveConflict?: (conflictId: string, data: VehicleVerificationConflictResolve) => void
  canResolve?: boolean
}

export function VehicleVerificationConflictsPanel({
  conflicts,
  onResolveConflict,
  canResolve = true,
}: PanelProps) {
  const [selectedConflict, setSelectedConflict] = useState<VehicleVerificationConflict | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const openConflicts = conflicts.filter((c) => c.status === 'OPEN' || c.status === 'UNDER_REVIEW')

  const handleResolve = (conflictId: string, data: VehicleVerificationConflictResolve) => {
    if (!onResolveConflict) return
    setSubmitting(true)
    try {
      onResolveConflict(conflictId, data)
      setSelectedConflict(null)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between">
        <h4 className="font-bold uppercase tracking-wider text-slate-500 text-xs">
          Discrepancias y Conflictos Detectados ({conflicts.length})
        </h4>
        {openConflicts.length > 0 && (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-3 py-1 font-bold text-rose-800 border border-rose-300">
            <LogisticsIcon name="alert" size={14} aria-hidden /> {openConflicts.length} Abiertos
          </span>
        )}
      </div>

      {conflicts.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-slate-400">
          No existen conflictos de datos registrados para este vehículo.
        </div>
      ) : (
        <div className="space-y-3">
          {conflicts.map((c) => (
            <div
              key={c.id}
              className={`rounded-2xl border p-4 bg-white shadow-xs space-y-3 ${
                c.status === 'OPEN' ? 'border-rose-200' : 'border-slate-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800 text-sm">{c.field_label || c.field_name}</span>
                  <span className="ml-2 text-slate-400">· Fuente: {c.source_name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded px-2 py-0.5 font-bold text-[10px] ${
                      c.severity === 'CRITICAL'
                        ? 'bg-rose-100 text-rose-800'
                        : c.severity === 'HIGH'
                        ? 'bg-orange-100 text-orange-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    Severidad {c.severity}
                  </span>
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-700 font-bold">
                    {c.status}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3 font-mono">
                <div>
                  <span className="font-sans font-bold text-[10px] text-slate-400 uppercase block">Valor Actual en Maestro:</span>
                  <span className="text-slate-800">{c.master_value || '—'}</span>
                </div>
                <div>
                  <span className="font-sans font-bold text-[10px] text-slate-400 uppercase block">Valor Verificado Oficial:</span>
                  <span className="text-indigo-700 font-bold">{c.verified_value || '—'}</span>
                </div>
              </div>

              {c.status === 'OPEN' && canResolve && (
                <div className="flex justify-end pt-1">
                  <Button size="small" variant="secondary" onClick={() => setSelectedConflict(c)}>
                    Resolver Conflicto (Step-Up)
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedConflict && (
        <ResolveVehicleVerificationConflictDialog
          isOpen={Boolean(selectedConflict)}
          isSubmitting={submitting}
          conflict={selectedConflict}
          onResolve={(data) => handleResolve(selectedConflict.id, data)}
          onClose={() => setSelectedConflict(null)}
        />
      )}
    </div>
  )
}

interface ResolveDialogProps {
  isOpen: boolean
  isSubmitting: boolean
  conflict: VehicleVerificationConflict
  onResolve: (data: VehicleVerificationConflictResolve) => void
  onClose: () => void
}

export function ResolveVehicleVerificationConflictDialog({
  isOpen,
  isSubmitting,
  conflict,
  onResolve,
  onClose,
}: ResolveDialogProps) {
  const [strategy, setStrategy] = useState<'KEEP_MASTER' | 'APPLY_VERIFIED' | 'MANUAL_ENTRY' | 'DISMISS'>('KEEP_MASTER')
  const [manualValue, setManualValue] = useState('')
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim() || isSubmitting) return
    onResolve({
      resolution_strategy: strategy,
      manual_value: strategy === 'MANUAL_ENTRY' ? manualValue.trim() : undefined,
      reason: reason.trim(),
    })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="resolve-conflict-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="resolve-conflict-title" className="text-base font-bold text-slate-800">
          Resolver Discrepancia: {conflict.field_label || conflict.field_name}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Estrategia de Resolución *</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as 'KEEP_MASTER' | 'APPLY_VERIFIED' | 'MANUAL_ENTRY' | 'DISMISS')}
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white font-bold"
            >
              <option value="KEEP_MASTER">Mantener valor actual del maestro ({conflict.master_value})</option>
              <option value="APPLY_VERIFIED">Aplicar valor verificado ({conflict.verified_value})</option>
              <option value="MANUAL_ENTRY">Ingresar valor manual corregido</option>
              <option value="DISMISS">Descartar conflicto sin modificar maestro</option>
            </select>
          </div>

          {strategy === 'MANUAL_ENTRY' && (
            <div>
              <label className="mb-1 block font-bold text-slate-700">Valor Manual Corregido *</label>
              <input
                type="text"
                value={manualValue}
                onChange={(e) => setManualValue(e.target.value)}
                required
                className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
          )}

          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo de Resolución *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              required
              placeholder="Justificación del dictamen de resolución..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!reason.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Resolviendo..."
            >
              Confirmar Resolución (Step-Up)
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
