import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { vehicleVerificationsApi } from '../api/vehicle-verifications-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { VehicleVerificationFreshnessIndicator } from '../components/vehicle-verifications/VehicleVerificationFreshnessIndicator'
import { VehicleVerificationSourceBadge } from '../components/vehicle-verifications/VehicleVerificationSourceBadge'
import type { PaginatedResponse } from '../types/logistics-resources'
import { LogisticsIcon } from '../components/common/LogisticsIcon'
import type {
  VehicleVerificationDomain,
  VehicleVerificationFreshness,
  VehicleVerificationListQuery,
  VehicleVerificationSourceType,
  VehicleVerificationStats,
  VehicleVerificationSummary,
} from '../types/vehicle-verifications'

const PAGE_SIZE = 20

export function VehicleVerificationsPage() {
  const navigate = useNavigate()

  const [data, setData] = useState<PaginatedResponse<VehicleVerificationSummary> | null>(null)
  const [stats, setStats] = useState<VehicleVerificationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [plate, setPlate] = useState('')
  const [debouncedPlate, setDebouncedPlate] = useState('')
  const [page, setPage] = useState(1)

  // Filters
  const [domain, setDomain] = useState<VehicleVerificationDomain | ''>('')
  const [sourceType, setSourceType] = useState<VehicleVerificationSourceType | ''>('')
  const [freshness, setFreshness] = useState<VehicleVerificationFreshness | ''>('')

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedPlate(plate)
      setPage(1)
    }, 400)
    return () => clearTimeout(timer)
  }, [plate])

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const query: VehicleVerificationListQuery = {
        page,
        page_size: PAGE_SIZE,
        plate: debouncedPlate || undefined,
        domain: domain || undefined,
        source_type: sourceType || undefined,
        freshness: freshness || undefined,
      }
      const [res, statsRes] = await Promise.all([
        vehicleVerificationsApi.list(query),
        vehicleVerificationsApi.getStats().catch(() => null),
      ])
      setData(res)
      if (statsRes) setStats(statsRes)
    } finally {
      setLoading(false)
    }
  }, [page, debouncedPlate, domain, sourceType, freshness])

  useEffect(() => {
    void loadData()
  }, [loadData])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Panel General de Verificaciones Vehiculares"
        description="Auditoría de legalidad, vigencia registral (SUNARP), SOAT (SBS), inspección técnica (MTC) y autorizaciones."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => navigate('/logistics/integrations/vehicle-verifications/conflicts')}>
              Conflictos
            </Button>
            <Button variant="secondary" onClick={() => navigate('/logistics/integrations/vehicle-verifications/sources')}>
              Fuentes
            </Button>
            <Button variant="secondary" onClick={() => navigate('/logistics/integrations/vehicle-verifications/requirements')}>
              Requisitos
            </Button>
            <Button variant="secondary" onClick={() => navigate('/logistics/integrations/vehicle-verifications/review-tasks')}>
              Tareas
            </Button>
          </div>
        }
      />

      {/* Stats Summary Cards */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6 text-xs">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Total Verificaciones</span>
            <span className="font-mono text-xl font-bold text-slate-800">{stats.total_verifications}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Vigentes</span>
            <span className="font-mono text-xl font-bold text-emerald-700">{stats.fresh_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Por Vencer</span>
            <span className="font-mono text-xl font-bold text-amber-700">{stats.expiring_soon_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Vencidas</span>
            <span className="font-mono text-xl font-bold text-rose-600">{stats.expired_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Con Conflicto</span>
            <span className="font-mono text-xl font-bold text-rose-700">{stats.conflicted_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Fuentes Degradadas</span>
            <span className="font-mono text-xl font-bold text-slate-700">{stats.degraded_sources_count}</span>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs text-xs">
        <div className="flex flex-1 flex-wrap items-center gap-3">
          <input
            type="text"
            value={plate}
            onChange={(e) => setPlate(e.target.value)}
            placeholder="Filtrar por placa de rodaje..."
            className="w-full sm:w-60 font-mono uppercase font-bold rounded-xl border border-slate-300 px-3.5 py-2 placeholder:font-normal placeholder:text-slate-400"
          />

          <select
            value={domain}
            onChange={(e) => {
              setDomain(e.target.value as VehicleVerificationDomain | '')
              setPage(1)
            }}
            className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
          >
            <option value="">Todos los dominios</option>
            <option value="REGISTRO_PROPIEDAD">Identidad Registral</option>
            <option value="PROPIETARIO">Titular de Propiedad</option>
            <option value="REVISION_TECNICA">Revisión Técnica (CITV)</option>
            <option value="SOAT">SOAT Obligatorio</option>
            <option value="AUTORIZACION_TRANSPORTE">Autorización MTC</option>
          </select>

          <select
            value={sourceType}
            onChange={(e) => {
              setSourceType(e.target.value as VehicleVerificationSourceType | '')
              setPage(1)
            }}
            className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
          >
            <option value="">Todas las fuentes</option>
            <option value="SUNARP">SUNARP Registral</option>
            <option value="MTC">MTC Oficial</option>
            <option value="SBS">SBS / Seguros</option>
            <option value="ASSISTED_MANUAL">Validación Asistida</option>
          </select>

          <select
            value={freshness}
            onChange={(e) => {
              setFreshness(e.target.value as VehicleVerificationFreshness | '')
              setPage(1)
            }}
            className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
          >
            <option value="">Todas las vigencias</option>
            <option value="FRESH">Vigente</option>
            <option value="AGING">Envejeciendo</option>
            <option value="CRITICAL">Por Vencer</option>
            <option value="EXPIRED">Vencida</option>
          </select>
        </div>

        {(plate || domain || sourceType || freshness) && (
          <button
            type="button"
            onClick={() => {
              setPlate('')
              setDomain('')
              setSourceType('')
              setFreshness('')
              setPage(1)
            }}
            className="text-xs font-semibold text-indigo-600 hover:underline"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Main Table */}
      {loading ? (
        <LoadingSkeleton rows={8} />
      ) : !data || data.items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500">
          No se encontraron verificaciones registrales registradas.
        </div>
      ) : (
        <div className="space-y-4 text-xs">
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Placa</th>
                  <th className="px-4 py-3 text-left font-semibold">Dominio</th>
                  <th className="px-4 py-3 text-center font-semibold">Resultado</th>
                  <th className="px-4 py-3 text-left font-semibold">Fuente Oficial</th>
                  <th className="px-4 py-3 text-left font-semibold">Vigencia & Fechas</th>
                  <th className="px-4 py-3 text-center font-semibold">Conflictos</th>
                  <th className="px-4 py-3 text-right font-semibold">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {data.items.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => navigate(`/logistics/vehicles/${row.vehicle_id}?tab=verifications`)}
                    className="cursor-pointer hover:bg-slate-50/80 transition-colors"
                  >
                    <td className="px-4 py-3 font-mono font-bold text-slate-900 text-sm">
                      {row.plate_number}
                      <span className="text-slate-400 block text-[10px] font-normal font-sans">{row.make_model_summary}</span>
                    </td>
                    <td className="px-4 py-3 font-bold text-slate-800">{row.domain_label || row.domain}</td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                          row.result_status === 'VALIDATED'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : row.result_status === 'EXPIRED'
                            ? 'bg-rose-100 text-rose-800 border border-rose-300'
                            : 'bg-amber-100 text-amber-800 border border-amber-300'
                        }`}
                      >
                        {row.result_status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <VehicleVerificationSourceBadge sourceType={row.source_type} sourceName={row.source_name} size="sm" />
                    </td>
                    <td className="px-4 py-3">
                      <VehicleVerificationFreshnessIndicator
                        freshness={row.freshness}
                        expirationDate={row.expiration_date}
                        size="sm"
                      />
                    </td>
                    <td className="px-4 py-3 text-center">
                      {row.conflicts_count > 0 ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 font-mono text-[10px] font-bold text-rose-800 border border-rose-300">
                          <LogisticsIcon name="alert" size={14} aria-hidden /> {row.conflicts_count}
                        </span>
                      ) : (
                        <span className="text-slate-300">0</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/logistics/vehicles/${row.vehicle_id}?tab=verifications`)
                        }}
                        className="font-semibold text-indigo-600 hover:underline"
                      >
                        Ver Ficha →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination
            page={data.page}
            totalPages={data.total_pages}
            total={data.total}
            onPageChange={setPage}
          />
        </div>
      )}
    </div>
  )
}
