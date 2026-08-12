import { useState } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type { VehicleVerification } from '../../types/vehicle-verifications'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  verification: VehicleVerification
  currentVehicleVersion: number
  onApply: (selectedFields: string[], reason: string, expectedVersion: number) => void
  onClose: () => void
}

export function ApplyVehicleVerificationDialog({
  isOpen,
  isSubmitting,
  verification,
  currentVehicleVersion,
  onApply,
  onClose,
}: Props) {
  const [selectedFields, setSelectedFields] = useState<string[]>([]) // empty by default
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const toggleField = (fieldName: string) => {
    setSelectedFields((prev) =>
      prev.includes(fieldName) ? prev.filter((f) => f !== fieldName) : [...prev, fieldName],
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedFields.length === 0 || !reason.trim() || isSubmitting) return
    onApply(selectedFields, reason.trim(), currentVehicleVersion)
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
        className="w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="apply-verification-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="apply-verification-title" className="text-base font-bold text-slate-800">
          Aplicar Datos Verificados al Vehículo (Placa: {verification.plate_number})
        </h3>

        <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-blue-900 space-y-1">
          <p>
            Selecciona individualmente los campos verificados que deseas actualizar en la ficha del vehículo.
            La aplicación creará una nueva versión inmutable (v{currentVehicleVersion + 1}).
          </p>
          <p className="text-[11px] text-blue-800 flex items-start gap-1.5">
            <LogisticsIcon name="alert" size={14} aria-hidden /> <span><strong>Nota:</strong> El cambio de placa de rodaje NO se realiza desde este diálogo. Utiliza el flujo específico de cambio de placa (Fase 027).</span>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-bold text-slate-700 text-xs">Campos Verificados Disponibles para Aplicar:</h4>
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-3 py-2 text-center font-semibold">Seleccionar</th>
                    <th className="px-3 py-2 text-left font-semibold">Campo</th>
                    <th className="px-3 py-2 text-left font-semibold">Valor Actual</th>
                    <th className="px-3 py-2 text-left font-semibold">Valor Verificado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {verification.provenance_fields.map((field) => (
                    <tr key={field.field_name} className="hover:bg-slate-50">
                      <td className="px-3 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={selectedFields.includes(field.field_name)}
                          onChange={() => toggleField(field.field_name)}
                          className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="px-3 py-2 font-bold text-slate-800">{field.field_label || field.field_name}</td>
                      <td className="px-3 py-2 font-mono text-slate-500">{field.master_value || '—'}</td>
                      <td className="px-3 py-2 font-mono font-bold text-indigo-700">{field.verified_value || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo Obligatorio del Cambio *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              required
              placeholder="Indica la justificación administrativa para actualizar los atributos..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={selectedFields.length === 0 || !reason.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Aplicando con Step-Up..."
            >
              Aplicar {selectedFields.length} Campos (Step-Up)
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
