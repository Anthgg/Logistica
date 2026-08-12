import { useState } from 'react'
import { Button } from '../common/Button'
import type {
  AssistedVehicleVerificationCreate,
  VehicleVerificationDomain,
  VehicleVerificationResultStatus,
  VehicleVerificationSourceType,
} from '../../types/vehicle-verifications'

interface FormProps {
  vehicleId: string
  plateNumber: string
  onSubmit: (data: AssistedVehicleVerificationCreate) => void
  isSubmitting?: boolean
  onCancel?: () => void
}

export function AssistedVehicleVerificationForm({
  vehicleId,
  plateNumber,
  onSubmit,
  isSubmitting = false,
  onCancel,
}: FormProps) {
  const [domain, setDomain] = useState<VehicleVerificationDomain>('REGISTRO_PROPIEDAD')
  const [sourceType, setSourceType] = useState<VehicleVerificationSourceType>('SUNARP')
  const [refNumber, setRefNumber] = useState('')
  const [observedPlate, setObservedPlate] = useState(plateNumber)
  const [observedOwner, setObservedOwner] = useState('')
  const [observedMake, setObservedMake] = useState('')
  const [observedModel, setObservedModel] = useState('')
  const [observedYear, setObservedYear] = useState<number | undefined>(undefined)
  const [observedStatus, setObservedStatus] = useState('VIGENTE')
  const [expirationDate, setExpirationDate] = useState('')
  const [resultStatus, setResultStatus] = useState<VehicleVerificationResultStatus>('VALIDATED')
  const [notes, setNotes] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!refNumber.trim() || !notes.trim() || isSubmitting) return

    onSubmit({
      vehicle_id: vehicleId,
      plate_number: plateNumber,
      domain,
      source_type: sourceType,
      official_reference_number: refNumber.trim(),
      observation_timestamp: new Date().toISOString(),
      observed_plate: observedPlate.trim().toUpperCase(),
      observed_owner_name: observedOwner.trim() || undefined,
      observed_make_name: observedMake.trim() || undefined,
      observed_model_name: observedModel.trim() || undefined,
      observed_year: observedYear,
      observed_status: observedStatus.trim(),
      observed_expiration_date: expirationDate || undefined,
      result_status: resultStatus,
      notes: notes.trim(),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4 text-xs">
      <div className="border-b border-slate-100 pb-3">
        <h3 className="text-sm font-bold text-slate-800">Registrar Validación Asistida Oficial</h3>
        <p className="text-slate-500 text-[11px] mt-0.5">
          Ingresa los datos observados tras consultar manualmente la fuente autorizada. No copies respuestas HTML ni CAPTCHA.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <label className="mb-1 block font-bold text-slate-700">Dominio Normativo *</label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value as VehicleVerificationDomain)}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
          >
            <option value="REGISTRO_PROPIEDAD">Identidad Registral</option>
            <option value="PROPIETARIO">Titular de Propiedad</option>
            <option value="CARACTERISTICAS">Ficha Físico-Técnica</option>
            <option value="REVISION_TECNICA">Revisión Técnica (CITV)</option>
            <option value="SOAT">SOAT Obligatorio</option>
            <option value="AUTORIZACION_TRANSPORTE">Autorización MTC</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Fuente Consultada *</label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as VehicleVerificationSourceType)}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
          >
            <option value="SUNARP">SUNARP Portal Oficial</option>
            <option value="MTC">MTC Plataforma Oficial</option>
            <option value="SBS">SBS Portal SOAT</option>
            <option value="ASSISTED_MANUAL">Revisión Manual Asistida</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Nº Trámite / Constancia *</label>
          <input
            type="text"
            value={refNumber}
            onChange={(e) => setRefNumber(e.target.value)}
            placeholder="Ej. SUNARP-2026-99482"
            required
            className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Placa Observada *</label>
          <input
            type="text"
            value={observedPlate}
            onChange={(e) => setObservedPlate(e.target.value.toUpperCase())}
            required
            className="w-full font-mono uppercase font-bold rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Propietario Observado</label>
          <input
            type="text"
            value={observedOwner}
            onChange={(e) => setObservedOwner(e.target.value)}
            placeholder="Nombre o razón social observada..."
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Marca Observada</label>
          <input
            type="text"
            value={observedMake}
            onChange={(e) => setObservedMake(e.target.value)}
            placeholder="Ej. VOLVO"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Modelo Observado</label>
          <input
            type="text"
            value={observedModel}
            onChange={(e) => setObservedModel(e.target.value)}
            placeholder="Ej. FH16"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Año Observado</label>
          <input
            type="number"
            min={1900}
            max={2100}
            value={observedYear ?? ''}
            onChange={(e) => setObservedYear(e.target.value ? Number(e.target.value) : undefined)}
            placeholder="Ej. 2023"
            className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Estado Observado</label>
          <input
            type="text"
            value={observedStatus}
            onChange={(e) => setObservedStatus(e.target.value)}
            placeholder="Ej. VIGENTE, OBSERVADO"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Resultado de la Consulta *</label>
          <select
            value={resultStatus}
            onChange={(e) => setResultStatus(e.target.value as VehicleVerificationResultStatus)}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white font-bold"
          >
            <option value="VALIDATED">VÁLIDO (Coincide completamente)</option>
            <option value="OBSERVED">OBSERVADO (Diferencias menores)</option>
            <option value="MISMATCH">DISCREPANCIA (No coincide)</option>
            <option value="EXPIRED">VENCIDO</option>
            <option value="NOT_FOUND">NO ENCONTRADO</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Fecha de Vencimiento Observada</label>
          <input
            type="date"
            value={expirationDate}
            onChange={(e) => setExpirationDate(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block font-bold text-slate-700">Observaciones y Contexto Oficial *</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          required
          placeholder="Detalla los hallazgos de la consulta manual..."
          className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
        />
      </div>

      <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancelar
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting} loadingLabel="Registrando...">
          Registrar Validación Asistida
        </Button>
      </div>
    </form>
  )
}
