import { LogisticsIcon } from '../common/LogisticsIcon'
import type {
  VehicleVerification,
  VehicleVerificationDomain,
} from '../../types/vehicle-verifications'
import { VehicleVerificationFreshnessIndicator } from './VehicleVerificationFreshnessIndicator'
import { VehicleVerificationSourceBadge } from './VehicleVerificationSourceBadge'

interface Props {
  verifications: VehicleVerification[]
  onSelectDomain?: (verification: VehicleVerification) => void
  onRequestDomain?: (domain: VehicleVerificationDomain) => void
  canRequest?: boolean
}

const ALL_DOMAINS: { domain: VehicleVerificationDomain; label: string; description: string }[] = [
  { domain: 'REGISTRO_PROPIEDAD', label: 'Identidad Registral', description: 'Inscripción y partida registral oficial' },
  { domain: 'PROPIETARIO', label: 'Titular de Propiedad', description: 'Propietario legal o arrendatario actual' },
  { domain: 'CARACTERISTICAS', label: 'Ficha Físico-Técnica', description: 'Marca, modelo, VIN, ejes, peso y motor' },
  { domain: 'ESTADO_REGISTRAL', label: 'Estado Registral', description: 'Vigencia de la partida en registros públicos' },
  { domain: 'GRAVAMENES', label: 'Gravámenes / Requisitos', description: 'Embargos, garantias mobiliarias o robos' },
  { domain: 'AUTORIZACION_TRANSPORTE', label: 'Autorización MTC', description: 'Permiso oficial de transporte de mercancías' },
  { domain: 'HABILITACION_CARRIER', label: 'Habilitación Vehicular', description: 'Constancia de inscripción del transportista' },
  { domain: 'REVISION_TECNICA', label: 'Revisión Técnica (CITV)', description: 'Certificado de inspección técnica vigente' },
  { domain: 'SOAT', label: 'SOAT Obligatorio', description: 'Seguro obligatorio de accidentes de tránsito' },
  { domain: 'CAT', label: 'CAT Regional', description: 'Certificado de accidente de tránsito regional' },
  { domain: 'SEGURO', label: 'Póliza de Seguro', description: 'Seguro complementario de carga o responsabilidad' },
  { domain: 'PERMISO_OPERATIVO', label: 'Permiso Operativo', description: 'Permiso municipal o sectorial especial' },
  { domain: 'REFRIGERACION', label: 'Certificado Frigorífico', description: 'Homologación de cámara de congelados' },
  { domain: 'MERCANCIAS_PELIGROSAS', label: 'Mercancías Peligrosas (MATPEL)', description: 'Resolución de autorización para carga peligrosa' },
]

export function VehicleVerificationDomainsGrid({
  verifications,
  onSelectDomain,
  onRequestDomain,
  canRequest = true,
}: Props) {
  // Map latest verification by domain
  const verificationsMap = new Map<VehicleVerificationDomain, VehicleVerification>()
  verifications.forEach((v) => {
    if (!verificationsMap.has(v.domain)) {
      verificationsMap.set(v.domain, v)
    }
  })

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div>
          <h4 className="font-bold text-slate-800 text-sm">Matriz de Verificación por Dominios Normativos</h4>
          <p className="text-slate-500 text-[11px] mt-0.5">
            Evaluación independiente por dominio. No se emite un badge único simplificado.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Dominio Normativo</th>
              <th className="px-4 py-3 text-center font-semibold">Resultado</th>
              <th className="px-4 py-3 text-left font-semibold">Fuente Oficial</th>
              <th className="px-4 py-3 text-left font-semibold">Vigencia & Fechas</th>
              <th className="px-4 py-3 text-center font-semibold">Confianza</th>
              <th className="px-4 py-3 text-center font-semibold">Conflictos</th>
              <th className="px-4 py-3 text-right font-semibold">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {ALL_DOMAINS.map((row) => {
              const verification = verificationsMap.get(row.domain)

              return (
                <tr key={row.domain} className="hover:bg-slate-50/80 transition-colors">
                  {/* Domain Info */}
                  <td className="px-4 py-3">
                    <span className="font-bold text-slate-800 block text-xs">{row.label}</span>
                    <span className="text-[10px] text-slate-400 block">{row.description}</span>
                  </td>

                  {/* Result Status */}
                  <td className="px-4 py-3 text-center">
                    {verification ? (
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                          verification.result_status === 'VALIDATED'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : verification.result_status === 'EXPIRED'
                            ? 'bg-rose-100 text-rose-800 border border-rose-300'
                            : verification.result_status === 'MISMATCH'
                            ? 'bg-red-100 text-red-800 border border-red-300'
                            : 'bg-amber-100 text-amber-800 border border-amber-300'
                        }`}
                      >
                        {verification.result_status}
                      </span>
                    ) : (
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                        Pendiente
                      </span>
                    )}
                  </td>

                  {/* Source */}
                  <td className="px-4 py-3">
                    {verification ? (
                      <VehicleVerificationSourceBadge
                        sourceType={verification.source_type}
                        sourceName={verification.source_name}
                        size="sm"
                      />
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>

                  {/* Freshness & Dates */}
                  <td className="px-4 py-3">
                    {verification ? (
                      <VehicleVerificationFreshnessIndicator
                        freshness={verification.freshness}
                        sourceDate={verification.source_date}
                        expirationDate={verification.expires_at}
                        daysUntilExpiration={verification.days_until_expiration}
                        size="sm"
                      />
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>

                  {/* Confidence Score */}
                  <td className="px-4 py-3 text-center font-mono font-bold">
                    {verification && verification.confidence_score !== null ? (
                      <span
                        className={
                          verification.confidence_score >= 0.85
                            ? 'text-emerald-700'
                            : verification.confidence_score >= 0.6
                            ? 'text-amber-700'
                            : 'text-rose-700'
                        }
                      >
                        {Math.round(verification.confidence_score * 100)}%
                      </span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>

                  {/* Conflicts */}
                  <td className="px-4 py-3 text-center">
                    {verification && verification.conflicts_count > 0 ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 font-mono text-[10px] font-bold text-rose-800 border border-rose-300">
                        <LogisticsIcon name="alert" size={14} aria-hidden /> {verification.conflicts_count}
                      </span>
                    ) : (
                      <span className="text-slate-300">0</span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      {verification && onSelectDomain && (
                        <button
                          type="button"
                          onClick={() => onSelectDomain(verification)}
                          className="font-semibold text-indigo-600 hover:underline"
                        >
                          Ver Detalle
                        </button>
                      )}
                      {onRequestDomain && canRequest && (
                        <button
                          type="button"
                          onClick={() => onRequestDomain(row.domain)}
                          className="font-semibold text-slate-600 hover:text-indigo-600 hover:underline"
                        >
                          {verification ? 'Reverificar' : 'Solicitar'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
