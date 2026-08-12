import { useState } from 'react'
import { Button } from '../common/Button'
import type {
  AssistedVerificationCreate,
  RucDomicileCondition,
  RucSourceType,
  RucTaxpayerStatus,
} from '../../types/ruc-integration'

interface Props {
  onSubmit: (data: AssistedVerificationCreate) => void
  isSubmitting?: boolean
  initialRuc?: string
  partnerId?: string
}

export function AssistedRucVerificationForm({
  onSubmit,
  isSubmitting = false,
  initialRuc = '',
  partnerId,
}: Props) {
  const [ruc, setRuc] = useState(initialRuc)
  const [reason, setReason] = useState('')
  const [sourceType, setSourceType] = useState<RucSourceType>('ASSISTED_REVIEW')
  const [referenceNumber, setReferenceNumber] = useState('')
  const [reviewedAt, setReviewedAt] = useState(new Date().toISOString().slice(0, 16))
  const [observedLegalName, setObservedLegalName] = useState('')
  const [observedStatus, setObservedStatus] = useState<RucTaxpayerStatus>('ACTIVO')
  const [observedCondition, setObservedCondition] = useState<RucDomicileCondition>('HABIDO')
  const [observedUbigeo, setObservedUbigeo] = useState('')
  const [result, setResult] = useState<'APPROVED' | 'REJECTED' | 'OBSERVED'>('APPROVED')
  const [observations, setObservations] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!ruc || !reason || !observedLegalName || isSubmitting) return

    onSubmit({
      ruc,
      partner_id: partnerId,
      reason,
      source_type: sourceType,
      reference_number: referenceNumber || undefined,
      reviewed_at: reviewedAt,
      observed_legal_name: observedLegalName,
      observed_status: observedStatus,
      observed_condition: observedCondition,
      observed_ubigeo: observedUbigeo,
      result,
      observations,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4 text-xs">
      <div className="border-b border-slate-100 pb-3">
        <h3 className="text-sm font-bold text-slate-800">Registrar Validación Asistida</h3>
        <p className="text-slate-500 mt-0.5">
          Realiza la revisión manual en la fuente oficial e ingresa los hallazgos para auditar el expediente.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block font-bold text-slate-700">RUC *</label>
          <input
            type="text"
            inputMode="numeric"
            maxLength={11}
            value={ruc}
            onChange={(e) => setRuc(e.target.value)}
            required
            className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2 text-xs"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Motivo de revisión *</label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Ej. Contingencia de API, padrón desactualizado..."
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Fecha y Hora de Revisión *</label>
          <input
            type="datetime-local"
            value={reviewedAt}
            onChange={(e) => setReviewedAt(e.target.value)}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Razón Social observada *</label>
          <input
            type="text"
            value={observedLegalName}
            onChange={(e) => setObservedLegalName(e.target.value)}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Tipo de Fuente *</label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as RucSourceType)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white"
          >
            <option value="ASSISTED_REVIEW">Validación asistida</option>
            <option value="OFFICIAL_PADRON">Padrón reducido oficial</option>
            <option value="AUTHORIZED_PROVIDER">Proveedor autorizado</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Nº de Expediente / Referencia</label>
          <input
            type="text"
            value={referenceNumber}
            onChange={(e) => setReferenceNumber(e.target.value)}
            placeholder="Ej. EXP-2026-88"
            className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2 text-xs"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Estado observado</label>
          <select
            value={observedStatus}
            onChange={(e) => setObservedStatus(e.target.value as RucTaxpayerStatus)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white"
          >
            <option value="ACTIVO">ACTIVO</option>
            <option value="BAJA_PROVISIONAL">BAJA PROVISIONAL</option>
            <option value="BAJA_DEFINITIVA">BAJA DEFINITIVA</option>
            <option value="SUSPENSION_TEMPORAL">SUSPENSIÓN TEMPORAL</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Condición observada</label>
          <select
            value={observedCondition}
            onChange={(e) => setObservedCondition(e.target.value as RucDomicileCondition)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white"
          >
            <option value="HABIDO">HABIDO</option>
            <option value="NO_HABIDO">NO HABIDO</option>
            <option value="NO_HALLADO">NO HALLADO</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Ubigeo observado</label>
          <input
            type="text"
            value={observedUbigeo}
            onChange={(e) => setObservedUbigeo(e.target.value)}
            placeholder="Ej. 150101"
            className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2 text-xs"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Dictamen preliminar</label>
          <select
            value={result}
            onChange={(e) => setResult(e.target.value as 'APPROVED' | 'REJECTED' | 'OBSERVED')}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white"
          >
            <option value="APPROVED">CONFORME / APROBADO</option>
            <option value="OBSERVED">OBSERVADO</option>
            <option value="REJECTED">NO CONFORME / RECHAZADO</option>
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1 block font-bold text-slate-700">Observaciones detalladas</label>
        <textarea
          value={observations}
          onChange={(e) => setObservations(e.target.value)}
          rows={2}
          placeholder="Anota cualquier detalle relevante para la posterior revisión o aprobación..."
          className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-xs"
        />
      </div>

      <div className="flex justify-end pt-2">
        <Button
          type="submit"
          disabled={!ruc || !reason || !observedLegalName || isSubmitting}
          isLoading={isSubmitting}
          loadingLabel="Registrando..."
        >
          Registrar Validación Asistida
        </Button>
      </div>
    </form>
  )
}
