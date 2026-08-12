import { useState } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type {
  VehicleVerificationDomain,
  VehicleVerificationRequirement,
  VehicleVerificationRequirementCreate,
  VehicleVerificationRequirementUpdate,
  VehicleVerificationSourceType,
} from '../../types/vehicle-verifications'

interface Props {
  initial?: VehicleVerificationRequirement
  isSubmitting?: boolean
  onSubmit: (data: VehicleVerificationRequirementCreate | VehicleVerificationRequirementUpdate) => void
  onCancel?: () => void
}

const DOMAIN_OPTIONS: { value: VehicleVerificationDomain; label: string }[] = [
  { value: 'REGISTRO_PROPIEDAD', label: 'Identidad Registral' },
  { value: 'PROPIETARIO', label: 'Titular de Propiedad' },
  { value: 'CARACTERISTICAS', label: 'Ficha Físico-Técnica' },
  { value: 'ESTADO_REGISTRAL', label: 'Estado Registral' },
  { value: 'GRAVAMENES', label: 'Gravámenes / Requisitos' },
  { value: 'AUTORIZACION_TRANSPORTE', label: 'Autorización MTC' },
  { value: 'HABILITACION_CARRIER', label: 'Habilitación Vehicular' },
  { value: 'REVISION_TECNICA', label: 'Revisión Técnica (CITV)' },
  { value: 'SOAT', label: 'SOAT Obligatorio' },
  { value: 'CAT', label: 'CAT Regional' },
  { value: 'SEGURO', label: 'Póliza de Seguro' },
  { value: 'PERMISO_OPERATIVO', label: 'Permiso Operativo' },
  { value: 'REFRIGERACION', label: 'Certificado Frigorífico' },
  { value: 'MERCANCIAS_PELIGROSAS', label: 'Mercancías Peligrosas (MATPEL)' },
]

const SOURCE_OPTIONS: { value: VehicleVerificationSourceType; label: string }[] = [
  { value: 'SUNARP', label: 'SUNARP' },
  { value: 'MTC', label: 'MTC' },
  { value: 'SBS', label: 'SBS' },
  { value: 'AUTHORIZED_PROVIDER', label: 'Proveedor Autorizado' },
  { value: 'ASSISTED_MANUAL', label: 'Validación Asistida' },
  { value: 'DOCUMENTARY_REVIEW', label: 'Revisión Documental' },
  { value: 'INTERNAL', label: 'Heredada / Interna' },
]

export function VehicleVerificationRequirementForm({ initial, isSubmitting = false, onSubmit, onCancel }: Props) {
  const isEdit = Boolean(initial)
  const [vehicleType, setVehicleType] = useState(initial?.vehicle_type ?? '')
  const [bodyType, setBodyType] = useState(initial?.body_type ?? '')
  const [ownershipType, setOwnershipType] = useState(initial?.ownership_type ?? '')
  const [carrierCategory, setCarrierCategory] = useState(initial?.carrier_category ?? '')
  const [domain, setDomain] = useState<VehicleVerificationDomain>(
    initial?.domain ?? 'REGISTRO_PROPIEDAD',
  )
  const [preferredSource, setPreferredSource] = useState<VehicleVerificationSourceType>(
    initial?.preferred_source ?? 'SUNARP',
  )
  const [isMandatory, setIsMandatory] = useState(initial?.is_mandatory ?? true)
  const [isBlocking, setIsBlocking] = useState(initial?.is_blocking ?? false)
  const [maxAgeDays, setMaxAgeDays] = useState(initial?.max_age_days ?? 365)
  const [warningDays, setWarningDays] = useState(initial?.warning_days ?? 30)
  const [minConfidence, setMinConfidence] = useState(initial?.min_confidence_score ?? 0.8)
  const [allowAssisted, setAllowAssisted] = useState(initial?.allow_assisted_validation ?? true)
  const [evidenceRequired, setEvidenceRequired] = useState(initial?.evidence_required ?? false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmitting) return
    if (isEdit) {
      const update: VehicleVerificationRequirementUpdate = {
        preferred_source: preferredSource,
        is_mandatory: isMandatory,
        is_blocking: isBlocking,
        max_age_days: maxAgeDays,
        warning_days: warningDays,
        min_confidence_score: minConfidence,
        allow_assisted_validation: allowAssisted,
        evidence_required: evidenceRequired,
      }
      onSubmit(update)
    } else {
      if (!vehicleType.trim()) return
      const create: VehicleVerificationRequirementCreate = {
        vehicle_type: vehicleType.trim(),
        body_type: bodyType.trim() || undefined,
        ownership_type: ownershipType.trim() || undefined,
        carrier_category: carrierCategory.trim() || undefined,
        domain,
        preferred_source: preferredSource,
        is_mandatory: isMandatory,
        is_blocking: isBlocking,
        max_age_days: maxAgeDays,
        warning_days: warningDays,
        min_confidence_score: minConfidence,
        allow_assisted_validation: allowAssisted,
        evidence_required: evidenceRequired,
      }
      onSubmit(create)
    }
  }

  const isReadonlyActive = isEdit && initial?.status === 'ACTIVE'

  return (
    <form onSubmit={handleSubmit} className="space-y-4 text-xs">
      {isReadonlyActive && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-amber-800 flex items-start gap-1.5">
          <LogisticsIcon name="alert" size={14} aria-hidden /> <span>Este requisito está ACTIVE. No se puede editar directamente. Retíralo y crea uno nuevo, o edítalo en estado DRAFT.</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="req-vehicle-type" className="mb-1 block font-bold text-slate-700">
            Tipo de vehículo *
          </label>
          <input
            id="req-vehicle-type"
            type="text"
            value={vehicleType}
            onChange={(e) => setVehicleType(e.target.value)}
            disabled={isEdit}
            required
            placeholder="Ej. CAMION, REMOLQUE"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 disabled:bg-slate-100"
          />
        </div>

        <div>
          <label htmlFor="req-body-type" className="mb-1 block font-bold text-slate-700">
            Carrocería
          </label>
          <input
            id="req-body-type"
            type="text"
            value={bodyType}
            onChange={(e) => setBodyType(e.target.value)}
            disabled={isEdit}
            placeholder="Ej. PLATAFORMA, FURGON"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 disabled:bg-slate-100"
          />
        </div>

        <div>
          <label htmlFor="req-ownership" className="mb-1 block font-bold text-slate-700">
            Tipo de propiedad
          </label>
          <input
            id="req-ownership"
            type="text"
            value={ownershipType}
            onChange={(e) => setOwnershipType(e.target.value)}
            disabled={isEdit}
            placeholder="Ej. PROPIO, ARRENDADO"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 disabled:bg-slate-100"
          />
        </div>

        <div>
          <label htmlFor="req-carrier" className="mb-1 block font-bold text-slate-700">
            Categoría de transportista
          </label>
          <input
            id="req-carrier"
            type="text"
            value={carrierCategory}
            onChange={(e) => setCarrierCategory(e.target.value)}
            disabled={isEdit}
            placeholder="Ej. NACIONAL, REGIONAL"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 disabled:bg-slate-100"
          />
        </div>

        <div>
          <label htmlFor="req-domain" className="mb-1 block font-bold text-slate-700">
            Dominio *
          </label>
          <select
            id="req-domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value as VehicleVerificationDomain)}
            disabled={isEdit}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white disabled:bg-slate-100"
          >
            {DOMAIN_OPTIONS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="req-source" className="mb-1 block font-bold text-slate-700">
            Fuente preferida *
          </label>
          <select
            id="req-source"
            value={preferredSource}
            onChange={(e) => setPreferredSource(e.target.value as VehicleVerificationSourceType)}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
          >
            {SOURCE_OPTIONS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="req-max-age" className="mb-1 block font-bold text-slate-700">
            Antigüedad máxima (días) *
          </label>
          <input
            id="req-max-age"
            type="number"
            min={1}
            value={maxAgeDays}
            onChange={(e) => setMaxAgeDays(Number(e.target.value))}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono"
          />
        </div>

        <div>
          <label htmlFor="req-warning-days" className="mb-1 block font-bold text-slate-700">
            Días de advertencia *
          </label>
          <input
            id="req-warning-days"
            type="number"
            min={0}
            value={warningDays}
            onChange={(e) => setWarningDays(Number(e.target.value))}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono"
          />
        </div>

        <div>
          <label htmlFor="req-confidence" className="mb-1 block font-bold text-slate-700">
            Confianza mínima (0–1) *
          </label>
          <input
            id="req-confidence"
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={minConfidence}
            onChange={(e) => setMinConfidence(Number(e.target.value))}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <label className="flex items-center gap-2 rounded-xl border border-slate-200 p-3 cursor-pointer">
          <input
            type="checkbox"
            checked={isMandatory}
            onChange={(e) => setIsMandatory(e.target.checked)}
            className="rounded border-slate-300 text-indigo-600"
          />
          <span className="font-bold text-slate-700">Obligatoria</span>
        </label>
        <label className="flex items-center gap-2 rounded-xl border border-slate-200 p-3 cursor-pointer">
          <input
            type="checkbox"
            checked={isBlocking}
            onChange={(e) => setIsBlocking(e.target.checked)}
            className="rounded border-slate-300 text-indigo-600"
          />
          <span className="font-bold text-slate-700">Bloqueante</span>
        </label>
        <label className="flex items-center gap-2 rounded-xl border border-slate-200 p-3 cursor-pointer">
          <input
            type="checkbox"
            checked={allowAssisted}
            onChange={(e) => setAllowAssisted(e.target.checked)}
            className="rounded border-slate-300 text-indigo-600"
          />
          <span className="font-bold text-slate-700">Permitir asistida</span>
        </label>
        <label className="flex items-center gap-2 rounded-xl border border-slate-200 p-3 cursor-pointer">
          <input
            type="checkbox"
            checked={evidenceRequired}
            onChange={(e) => setEvidenceRequired(e.target.checked)}
            className="rounded border-slate-300 text-indigo-600"
          />
          <span className="font-bold text-slate-700">Evidencia obligatoria</span>
        </label>
      </div>

      <p className="text-[10px] text-slate-500 leading-relaxed">
        El backend valida y activa la política. No se codifican requisitos legales en el frontend.
      </p>

      <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancelar
          </Button>
        )}
        <Button type="submit" disabled={isSubmitting || isReadonlyActive} isLoading={isSubmitting} loadingLabel="Guardando...">
          {isEdit ? 'Guardar Cambios (DRAFT)' : 'Crear Requisito (DRAFT)'}
        </Button>
      </div>
    </form>
  )
}