import { useState } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { VehicleVerificationSourceBadge } from './VehicleVerificationSourceBadge'
import type {
  VehicleVerificationDomain,
  VehicleVerificationRequest,
  VehicleVerificationSourceType,
} from '../../types/vehicle-verifications'

interface SourceOption {
  source_type: VehicleVerificationSourceType
  source_name: string
  method: string
  authorization_status: string
  available: boolean
}

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  vehicleId: string
  plateNumber: string
  availableSources: readonly SourceOption[]
  defaultDomain?: VehicleVerificationDomain
  onSubmit: (data: VehicleVerificationRequest) => void
  onClose: () => void
}

const DOMAIN_OPTIONS: { value: VehicleVerificationDomain; label: string; dataChecked: string }[] = [
  { value: 'REGISTRO_PROPIEDAD', label: 'Identidad Registral', dataChecked: 'Partida registral, placa, estado' },
  { value: 'PROPIETARIO', label: 'Titular de Propiedad', dataChecked: 'Propietario inscrito, transferencias' },
  { value: 'CARACTERISTICAS', label: 'Ficha Físico-Técnica', dataChecked: 'Marca, modelo, VIN, motor, ejes' },
  { value: 'ESTADO_REGISTRAL', label: 'Estado Registral', dataChecked: 'Vigencia de inscripción registral' },
  { value: 'GRAVAMENES', label: 'Gravámenes / Requisitos', dataChecked: 'Embargos, garantías, robos' },
  { value: 'AUTORIZACION_TRANSPORTE', label: 'Autorización MTC', dataChecked: 'Permiso oficial de transporte' },
  { value: 'HABILITACION_CARRIER', label: 'Habilitación Vehicular', dataChecked: 'Constancia MTC del transportista' },
  { value: 'REVISION_TECNICA', label: 'Revisión Técnica (CITV)', dataChecked: 'Certificado de inspección técnica' },
  { value: 'SOAT', label: 'SOAT Obligatorio', dataChecked: 'Póliza SOAT vigente' },
  { value: 'CAT', label: 'CAT Regional', dataChecked: 'Certificado de accidente de tránsito' },
  { value: 'SEGURO', label: 'Póliza de Seguro', dataChecked: 'Seguro complementario de carga' },
  { value: 'PERMISO_OPERATIVO', label: 'Permiso Operativo', dataChecked: 'Permiso municipal o sectorial' },
  { value: 'REFRIGERACION', label: 'Certificado Frigorífico', dataChecked: 'Homologación de cámara fría' },
  { value: 'MERCANCIAS_PELIGROSAS', label: 'Mercancías Peligrosas (MATPEL)', dataChecked: 'Resolución MATPEL' },
]

export function RequestVehicleVerificationDialog({
  isOpen,
  isSubmitting,
  vehicleId,
  plateNumber,
  availableSources,
  defaultDomain = 'REGISTRO_PROPIEDAD',
  onSubmit,
  onClose,
}: Props) {
  const [domain, setDomain] = useState<VehicleVerificationDomain>(defaultDomain)
  const [preferredSource, setPreferredSource] = useState<VehicleVerificationSourceType | ''>('')
  const [allowProvider, setAllowProvider] = useState(false)
  const [reason, setReason] = useState('')
  const [purpose, setPurpose] = useState('')

  if (!isOpen) return null

  const domainMeta = DOMAIN_OPTIONS.find((d) => d.value === domain)
  const compatibleSources = availableSources.filter((s) => s.available)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim() || isSubmitting) return
    onSubmit({
      vehicle_id: vehicleId,
      plate_number: plateNumber,
      domain,
      preferred_source: preferredSource || undefined,
      allow_authorized_provider: allowProvider,
      reason: reason.trim(),
      purpose: purpose.trim() || undefined,
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
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="request-verification-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="request-verification-title" className="text-base font-bold text-slate-800">
          Solicitar Verificación Autorizada — Placa <span className="font-mono text-indigo-700">{plateNumber}</span>
        </h3>

        <p className="text-[11px] text-slate-500 leading-relaxed">
          La consulta es procesada por el backend a través de fuentes autorizadas. React no consulta portales externos,
          no automatiza CAPTCHA ni expone credenciales.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="rq-domain" className="mb-1 block font-bold text-slate-700">
                Dominio Normativo *
              </label>
              <select
                id="rq-domain"
                value={domain}
                onChange={(e) => {
                  setDomain(e.target.value as VehicleVerificationDomain)
                  setPreferredSource('')
                }}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
              >
                {DOMAIN_OPTIONS.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="rq-source" className="mb-1 block font-bold text-slate-700">
                Fuente Preferida (opcional)
              </label>
              <select
                id="rq-source"
                value={preferredSource}
                onChange={(e) => setPreferredSource(e.target.value as VehicleVerificationSourceType | '')}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
              >
                <option value="">Selección automática por el backend</option>
                {compatibleSources.map((s) => (
                  <option key={s.source_type} value={s.source_type}>
                    {s.source_name} ({s.method})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <label className="flex items-start gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 cursor-pointer">
            <input
              type="checkbox"
              checked={allowProvider}
              onChange={(e) => setAllowProvider(e.target.checked)}
              className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-slate-700">
              <strong className="block">Permitir proveedor autorizado</strong>
              <span className="text-[10px] text-slate-500">
                Autoriza al backend a usar un proveedor autorizado si la fuente oficial no está disponible.
              </span>
            </span>
          </label>

          <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-1">
            <span className="font-bold text-slate-700 text-[11px] uppercase tracking-wider block">
              Datos que serán consultados
            </span>
            <p className="text-slate-600 font-mono text-[11px]">{domainMeta?.dataChecked ?? '—'}</p>
          </div>

          <div>
            <label htmlFor="rq-reason" className="mb-1 block font-bold text-slate-700">
              Motivo de la solicitud *
            </label>
            <input
              id="rq-reason"
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
              maxLength={200}
              placeholder="Ej. Verificación periódica de legalidad vehicular"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div>
            <label htmlFor="rq-purpose" className="mb-1 block font-bold text-slate-700">
              Finalidad (opcional)
            </label>
            <input
              id="rq-purpose"
              type="text"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              maxLength={200}
              placeholder="Ej. Incorporación de vehículo a flota"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          {compatibleSources.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-2">
              <span className="font-bold text-slate-700 text-[11px] uppercase tracking-wider block">
                Fuentes disponibles para este dominio
              </span>
              <ul className="space-y-1">
                {compatibleSources.map((s) => (
                  <li key={s.source_type} className="flex items-center justify-between gap-2">
                    <VehicleVerificationSourceBadge sourceType={s.source_type} sourceName={s.source_name} size="sm" />
                    <span className="text-[10px] text-slate-500 font-mono">
                      {s.method} · {s.authorization_status}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-amber-800 text-[11px] space-y-1">
            <p className="flex items-start gap-1.5">
              <LogisticsIcon name="alert" size={14} aria-hidden /> <span>No incluyas URLs, API keys, código HTML, CAPTCHA, valores de confianza ni resultados esperados. El backend determina la fuente oficial y la confianza.</span>
            </p>
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button type="submit" disabled={!reason.trim() || isSubmitting} isLoading={isSubmitting} loadingLabel="Solicitando...">
              Solicitar Verificación
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
