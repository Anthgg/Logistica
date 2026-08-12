import { useState } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { VehicleVerificationSourceBadge } from './VehicleVerificationSourceBadge'
import type { AssistedVehicleVerification } from '../../types/vehicle-verifications'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  verification: AssistedVehicleVerification
  proposedConfidence: number | null
  warnings: string[]
  differences: { field_label: string; master_value: string | null; observed_value: string | null }[]
  canSelfApprove: boolean
  onApprove: (notes: string) => void
  onReject: (reason: string) => void
  onClose: () => void
}

export function ApproveAssistedVehicleVerificationDialog({
  isOpen,
  isSubmitting,
  verification,
  proposedConfidence,
  warnings,
  differences,
  canSelfApprove,
  onApprove,
  onReject,
  onClose,
}: Props) {
  const [mode, setMode] = useState<'approve' | 'reject'>('approve')
  const [notes, setNotes] = useState('')
  const [rejectReason, setRejectReason] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmitting) return
    if (mode === 'approve') {
      if (!canSelfApprove) return
      onApprove(notes.trim())
    } else {
      if (!rejectReason.trim()) return
      onReject(rejectReason.trim())
    }
  }

  const maskedOwner = verification.observed_owner_name
    ? verification.observed_owner_name.length > 4
      ? `${verification.observed_owner_name.slice(0, 2)}***${verification.observed_owner_name.slice(-2)}`
      : '***'
    : '—'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="approve-assisted-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="approve-assisted-title" className="text-base font-bold text-slate-800">
          Revisar y Aprobar Validación Asistida
        </h3>

        {!canSelfApprove && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-rose-800 text-[11px] flex items-start gap-1.5">
            <LogisticsIcon name="lock" size={14} aria-hidden /> <span>El backend prohíbe aprobar tu propia validación asistida. Solo otro revisor autorizado puede aprobarla.</span>
          </div>
        )}

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700">Creador</span>
            <span className="font-bold text-slate-900">{verification.created_by_user_name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700">Fecha</span>
            <span className="font-mono text-slate-700">
              {new Date(verification.created_at).toLocaleString('es-PE')}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700">Fuente</span>
            <VehicleVerificationSourceBadge
              sourceType={verification.source_type}
              sourceName={verification.source_type}
              size="sm"
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700">Dominio</span>
            <span className="font-bold text-indigo-700">{verification.domain}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700">Resultado</span>
            <span className="font-bold text-slate-900">{verification.result_status}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700">Referencia oficial</span>
            <span className="font-mono text-slate-700">{verification.official_reference_number}</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-1">
          <span className="font-bold text-slate-700 text-[11px] uppercase tracking-wider block mb-1">
            Datos observados
          </span>
          <div className="grid grid-cols-2 gap-2 text-slate-700">
            <div>Placa: <strong className="font-mono">{verification.observed_plate}</strong></div>
            <div>Propietario: <strong className="font-mono">{maskedOwner}</strong></div>
            <div>Marca: <strong>{verification.observed_make_name || '—'}</strong></div>
            <div>Modelo: <strong>{verification.observed_model_name || '—'}</strong></div>
            <div>Año: <strong className="font-mono">{verification.observed_year ?? '—'}</strong></div>
            <div>Estado: <strong>{verification.observed_status}</strong></div>
            <div>Vencimiento: <strong className="font-mono">
              {verification.observed_expiration_date
                ? new Date(verification.observed_expiration_date).toLocaleDateString('es-PE')
                : '—'}
            </strong></div>
          </div>
          {verification.notes && (
            <p className="mt-2 text-slate-600 italic border-t border-slate-100 pt-2">"{verification.notes}"</p>
          )}
        </div>

        {differences.length > 0 && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-2">
            <span className="font-bold text-amber-800 text-[11px] uppercase tracking-wider block">
              Diferencias con el maestro
            </span>
            <ul className="space-y-1">
              {differences.map((d, idx) => (
                <li key={idx} className="flex flex-wrap items-center gap-2 text-amber-800">
                  <strong>{d.field_label}:</strong>
                  <span className="font-mono">{d.master_value || '—'}</span>
                  <span aria-hidden>→</span>
                  <span className="font-mono font-bold">{d.observed_value || '—'}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {proposedConfidence !== null && (
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-blue-800 text-[11px]">
            Confianza propuesta por el backend:{' '}
            <strong className="font-mono">{Math.round(proposedConfidence * 100)}%</strong>.
            El frontend no calcula confianza.
          </div>
        )}

        {warnings.length > 0 && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 space-y-1">
            <span className="font-bold text-rose-800 text-[11px] uppercase tracking-wider block">
              Advertencias
            </span>
            <ul className="list-disc list-inside text-rose-700">
              {warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setMode('approve')}
              className={`flex-1 rounded-xl border px-3 py-2 font-bold ${
                mode === 'approve'
                  ? 'border-emerald-300 bg-emerald-100 text-emerald-800'
                  : 'border-slate-200 bg-white text-slate-600'
              }`}
            >
              Aprobar
            </button>
            <button
              type="button"
              onClick={() => setMode('reject')}
              className={`flex-1 rounded-xl border px-3 py-2 font-bold ${
                mode === 'reject'
                  ? 'border-rose-300 bg-rose-100 text-rose-800'
                  : 'border-slate-200 bg-white text-slate-600'
              }`}
            >
              Rechazar
            </button>
          </div>

          {mode === 'approve' ? (
            <div>
              <label htmlFor="approve-notes" className="mb-1 block font-bold text-slate-700">
                Notas de aprobación
              </label>
              <textarea
                id="approve-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Notas opcionales del revisor..."
                className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
          ) : (
            <div>
              <label htmlFor="reject-reason" className="mb-1 block font-bold text-slate-700">
                Motivo de rechazo *
              </label>
              <textarea
                id="reject-reason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={2}
                required
                placeholder="Justifica el rechazo..."
                className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
          )}

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || (mode === 'approve' && !canSelfApprove) || (mode === 'reject' && !rejectReason.trim())}
              isLoading={isSubmitting}
              loadingLabel="Procesando con Step-Up..."
            >
              {mode === 'approve' ? 'Confirmar Aprobación (Step-Up)' : 'Confirmar Rechazo'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}