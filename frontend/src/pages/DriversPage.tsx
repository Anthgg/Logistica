import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { driversApi } from '../api/drivers-api'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { EmptyState } from '../components/common/EmptyState'
import { Pagination } from '../components/common/Pagination'
import { PageHeader } from '../components/common/PageHeader'
import { Alert } from '../components/common/Alert'
import {
  DriverComplianceBadge,
  DriverEligibilityBadge,
  DriverLifecycleBadge,
  ExpirationChip,
} from '../components/drivers/DriverStatusBadge'
import { DriverGeneralForm } from '../components/drivers/DriverGeneralForm'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { getErrorMessage } from '../utils/errors'
import type {
  DriverComplianceStatus,
  DriverCreate,
  DriverEligibilityStatus,
  DriverLifecycleStatus,
  DriverStats,
  DriverSummary,
  DriverUpdate,
} from '../types/drivers'
import type { PaginatedResponse } from '../types/logistics-resources'

const LIFECYCLE_OPTIONS: { value: DriverLifecycleStatus; label: string }[] = [
  { value: 'DRAFT', label: 'Borrador' },
  { value: 'ACTIVE', label: 'Activo' },
  { value: 'INACTIVE', label: 'Inactivo' },
  { value: 'SUSPENDED', label: 'Suspendido' },
  { value: 'BLOCKED', label: 'Bloqueado' },
  { value: 'RETIRED', label: 'Retirado' },
  { value: 'ARCHIVED', label: 'Archivado' },
]

const COMPLIANCE_OPTIONS: { value: DriverComplianceStatus; label: string }[] = [
  { value: 'UNEVALUATED', label: 'Sin evaluar' },
  { value: 'COMPLIANT', label: 'Cumple' },
  { value: 'PARTIAL', label: 'Parcial' },
  { value: 'NON_COMPLIANT', label: 'No cumple' },
  { value: 'DOCUMENTS_EXPIRED', label: 'Docs. vencidos' },
  { value: 'LICENSE_EXPIRED', label: 'Lic. vencida' },
  { value: 'UNDER_REVIEW', label: 'En revisión' },
]

const ELIGIBILITY_OPTIONS: { value: DriverEligibilityStatus; label: string }[] = [
  { value: 'UNEVALUATED', label: 'Sin evaluar' },
  { value: 'ELIGIBLE', label: 'Elegible' },
  { value: 'INELIGIBLE', label: 'No elegible' },
  { value: 'RESTRICTED', label: 'Restringido' },
  { value: 'UNDER_REVIEW', label: 'En revisión' },
]

function StatChip({ label, value, tone }: { label: string; value: number; tone: 'default' | 'warning' | 'danger' | 'success' }) {
  const tones = {
    default: 'border-slate-200 bg-slate-50 text-slate-700',
    warning: 'border-amber-200 bg-amber-50 text-amber-700',
    danger: 'border-rose-200 bg-rose-50 text-rose-700',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  }
  return (
    <div className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 ${tones[tone]}`}>
      <span className="text-xs font-medium">{label}</span>
      <span className="text-sm font-bold tabular-nums">{value}</span>
    </div>
  )
}

export function DriversPage() {
  const navigate = useNavigate()
  const auth = useLogisticsPermissions()
  const canCreate = auth.hasPermission(LOGISTICS_PERMISSIONS.drivers.create)

  const [data, setData] = useState<PaginatedResponse<DriverSummary>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [stats, setStats] = useState<DriverStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [lifecycleFilter, setLifecycleFilter] = useState('')
  const [complianceFilter, setComplianceFilter] = useState('')
  const [eligibilityFilter, setEligibilityFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  // Debounce search 400ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 400)
    return () => clearTimeout(timer)
  }, [search])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [listRes, statsRes] = await Promise.all([
        driversApi.list({
          page,
          page_size: 20,
          search: debouncedSearch || undefined,
          lifecycle_status: (lifecycleFilter || undefined) as DriverLifecycleStatus | undefined,
          compliance_status: (complianceFilter || undefined) as DriverComplianceStatus | undefined,
          eligibility_status: (eligibilityFilter || undefined) as DriverEligibilityStatus | undefined,
        }),
        driversApi.getStats().catch(() => null),
      ])
      setData(listRes)
      if (statsRes) setStats(statsRes)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [page, debouncedSearch, lifecycleFilter, complianceFilter, eligibilityFilter])

  useEffect(() => {
    void load()
  }, [load])

  const handleCreate = async (formData: DriverCreate | DriverUpdate) => {
    setCreating(true)
    setCreateError(null)
    try {
      const driver = await driversApi.create(formData as DriverCreate)
      setShowCreate(false)
      navigate(`/logistics/drivers/${driver.id}`)
    } catch (err) {
      setCreateError(getErrorMessage(err))
    } finally {
      setCreating(false)
    }
  }

  const clearFilters = () => {
    setSearch('')
    setLifecycleFilter('')
    setComplianceFilter('')
    setEligibilityFilter('')
    setPage(1)
  }

  const hasFilters = useMemo(
    () => Boolean(search || lifecycleFilter || complianceFilter || eligibilityFilter),
    [search, lifecycleFilter, complianceFilter, eligibilityFilter],
  )

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Conductores"
        description="Maestro de conductores del dominio logístico"
        actions={canCreate ? (
          <Button onClick={() => setShowCreate(true)}>+ Registrar conductor</Button>
        ) : undefined}
      />

      {/* Stats compactas */}
      {stats && !loading && (
        <div className="flex flex-wrap gap-2">
          <StatChip label="Total" value={stats.total_drivers} tone="default" />
          <StatChip label="Activos" value={stats.active_count} tone="success" />
          <StatChip label="Elegibles" value={stats.eligible_count} tone="success" />
          <StatChip label="Restringidos" value={stats.restricted_count} tone="warning" />
          <StatChip label="Lic. por vencer" value={stats.licenses_expiring_soon_count} tone="warning" />
          <StatChip label="Lic. vencidas" value={stats.licenses_expired_count} tone="danger" />
          <StatChip label="Docs. incompletos" value={stats.documents_incomplete_count} tone="warning" />
          <StatChip label="Bloqueados" value={stats.blocked_count} tone="danger" />
        </div>
      )}

      {/* Búsqueda y filtros */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <Input
            label="Buscar"
            placeholder="Código, nombre, documento, licencia, transportista, teléfono..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <select
            value={lifecycleFilter}
            onChange={(e) => { setLifecycleFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Estado</option>
            {LIFECYCLE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <select
            value={complianceFilter}
            onChange={(e) => { setComplianceFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Cumplimiento</option>
            {COMPLIANCE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <select
            value={eligibilityFilter}
            onChange={(e) => { setEligibilityFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Elegibilidad</option>
            {ELIGIBILITY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          {hasFilters && (
            <Button variant="ghost" onClick={clearFilters}>Limpiar</Button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && <Alert variant="error">{error}</Alert>}

      {/* Tabla */}
      {loading ? (
        <LoadingSkeleton rows={8} />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="No hay conductores"
          description={hasFilters ? 'No se encontraron conductores con los filtros aplicados.' : 'Aún no se ha registrado ningún conductor.'}
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Código</th>
                <th className="px-3 py-2">Conductor</th>
                <th className="px-3 py-2">Documento</th>
                <th className="px-3 py-2">Licencia</th>
                <th className="px-3 py-2 hidden md:table-cell">Categorías</th>
                <th className="px-3 py-2 hidden lg:table-cell">Vencimiento</th>
                <th className="px-3 py-2 hidden md:table-cell">Transportista</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2 hidden lg:table-cell">Cumplimiento</th>
                <th className="px-3 py-2 hidden xl:table-cell">Elegibilidad</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((driver) => (
                <tr
                  key={driver.id}
                  onClick={() => navigate(`/logistics/drivers/${driver.id}`)}
                  className="cursor-pointer hover:bg-slate-50 transition-colors"
                >
                  <td className="px-3 py-2 font-mono text-xs text-slate-500">{driver.internal_code}</td>
                  <td className="px-3 py-2 font-medium text-slate-900">{driver.full_name}</td>
                  <td className="px-3 py-2 text-slate-500">{driver.identity_document_number_redacted}</td>
                  <td className="px-3 py-2 text-slate-500">{driver.primary_license_number_redacted ?? '—'}</td>
                  <td className="px-3 py-2 hidden md:table-cell">
                    <div className="flex flex-wrap gap-1">
                      {driver.primary_license_categories.length > 0
                        ? driver.primary_license_categories.map((c) => (
                          <span key={c} className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">{c}</span>
                        ))
                        : <span className="text-xs text-slate-400">—</span>}
                    </div>
                  </td>
                  <td className="px-3 py-2 hidden lg:table-cell">
                    <ExpirationChip
                      days={driver.primary_license_is_expired ? null : null}
                      isExpired={driver.primary_license_is_expired}
                    />
                  </td>
                  <td className="px-3 py-2 hidden md:table-cell text-slate-600">{driver.carrier_partner_name ?? '—'}</td>
                  <td className="px-3 py-2"><DriverLifecycleBadge status={driver.lifecycle_status} /></td>
                  <td className="px-3 py-2 hidden lg:table-cell"><DriverComplianceBadge status={driver.compliance_status} /></td>
                  <td className="px-3 py-2 hidden xl:table-cell"><DriverEligibilityBadge status={driver.eligibility_status} /></td>
                  <td className="px-3 py-2">
                    {driver.restrictions_count > 0 && (
                      <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 border border-amber-300">
                        {driver.restrictions_count} restr.
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Paginación */}
      {!loading && data.total > 0 && (
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          total={data.total}
          onPageChange={setPage}
        />
      )}

      {/* Modal de creación */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm" onClick={() => { setShowCreate(false); setCreateError(null) }}>
          <div className="w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-900 p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-100">Registrar conductor</h2>
              <button type="button" onClick={() => { setShowCreate(false); setCreateError(null) }} className="text-slate-400 hover:text-white" aria-label="Cerrar"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
            </div>
            {createError && <div className="mb-4 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-sm text-rose-700">{createError}</div>}
            <DriverGeneralForm
              mode="create"
              onSubmit={handleCreate}
              onCancel={() => { setShowCreate(false); setCreateError(null) }}
              isSubmitting={creating}
            />
          </div>
        </div>
      )}
    </div>
  )
}