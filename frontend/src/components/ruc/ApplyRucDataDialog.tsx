import { useState } from 'react'
import { Button } from '../common/Button'
import type { ApplyRucDataRequest, RucLookupResponse } from '../../types/ruc-integration'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  lookupData: RucLookupResponse
  verificationId: string
  currentPartnerName: string
  error: string | null
  onApply: (req: ApplyRucDataRequest) => void
  onClose: () => void
}

export function ApplyRucDataDialog({
  isOpen,
  isSubmitting,
  lookupData,
  verificationId,
  currentPartnerName,
  error,
  onApply,
  onClose,
}: Props) {
  const [applyLegalName, setApplyLegalName] = useState(false)
  const [selectedAnnexAddress, setSelectedAnnexAddress] = useState('')
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim() || isSubmitting) return

    onApply({
      verification_id: verificationId,
      apply_legal_name: applyLegalName,
      apply_annex_as_candidate: Boolean(selectedAnnexAddress),
      selected_annex_address: selectedAnnexAddress || undefined,
      reason: reason.trim(),
    })
  }

  const isAnyFieldSelected = applyLegalName || Boolean(selectedAnnexAddress)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-5"
        role="dialog"
        aria-modal="true"
        aria-labelledby="apply-data-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-indigo-600">
              Sincronización Campo por Campo
            </p>
            <h3 id="apply-data-title" className="text-lg font-bold text-slate-800">
              Aplicar datos de RUC {lookupData.ruc}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-xs text-slate-600">
            Selecciona de manera independiente los campos que deseas actualizar en la ficha de{' '}
            <strong>{currentPartnerName}</strong>.
          </p>

          <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/50 p-4 text-xs">
            {/* Legal Name */}
            <label className="flex items-start gap-3 cursor-pointer p-2 rounded-lg hover:bg-white transition-colors">
              <input
                type="checkbox"
                checked={applyLegalName}
                onChange={(e) => setApplyLegalName(e.target.checked)}
                disabled={isSubmitting}
                className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              <div className="flex-1 space-y-0.5">
                <span className="font-semibold text-slate-800">Razón Social</span>
                <p className="text-slate-500 font-mono text-[11px]">{lookupData.legal_name}</p>
              </div>
            </label>

            {lookupData.annex_addresses.length > 0 && (
              <div className="space-y-1 p-2">
                <label htmlFor="annex-address" className="font-semibold text-slate-800">
                  Dirección anexa como candidata
                </label>
                <select
                  id="annex-address"
                  value={selectedAnnexAddress}
                  onChange={(event) => setSelectedAnnexAddress(event.target.value)}
                  disabled={isSubmitting}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs"
                >
                  <option value="">No aplicar dirección anexa</option>
                  {lookupData.annex_addresses.map((annex) => (
                    <option key={annex.id} value={annex.address}>
                      {annex.address}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div>
            <label htmlFor="apply-reason" className="mb-1 block text-xs font-bold text-slate-700">
              Motivo de la actualización *
            </label>
            <textarea
              id="apply-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              required
              placeholder="Ej. Sincronización periódica con padrón oficial..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!isAnyFieldSelected || !reason.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Aplicando..."
            >
              Aplicar Campos Seleccionados
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
