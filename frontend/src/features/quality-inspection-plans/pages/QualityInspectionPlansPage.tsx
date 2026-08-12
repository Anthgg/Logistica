import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { MetricCard } from '../../../components/common/MetricCard'
import { Pagination } from '../../../components/common/Pagination'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { EmptyState } from '../../../components/common/EmptyState'
import { Alert } from '../../../components/common/Alert'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { getErrorMessage } from '../../../utils/errors'
import type {
  QualityInspectionPlan,
  QualityInspectionPlanStatus,
  QualityInspectionPlanFamily,
  QualityPlanListQuery,
  PaginatedResponse,
  QualityInspectionPlanSummary,
} from '../types/quality-inspection-plans'

type TabKey = 'all' | 'drafts' | 'validated' | 'scheduled' | 'active' | 'retired' | 'archived' | 'conflicts'

const TABS: { key: TabKey; label: string; status?: QualityInspectionPlanStatus }[] = [
  { key: 'all', label: 'Todos' },
  { key: 'drafts', label: 'Borradores', status: 'DRAFT' },
  { key: 'validated', label: 'Validados', status: 'VALIDATED' },
  { key: 'scheduled', label: 'Programados', status: 'SCHEDULED' },
  { key: 'active', label: 'Activos', status: 'ACTIVE' },
  { key: 'retired', label: 'Retirados', status: 'RETIRED' },
  { key: 'archived', label: 'Archivados', status: 'ARCHIVED' },
  { key: 'conflicts', label: 'Con conflictos' },
]

const FAMILY_OPTIONS: { value: QualityInspectionPlanFamily; label: string }[] = [
  { value: 'GENERAL', label: 'General' },
  { value: 'PRODUCT', label: 'Producto' },
  { value: 'CATEGORY', label: 'Categoría' },
  { value: 'WAREHOUSE', label: 'Almacén' },
  { value: 'SUPPLIER', label: 'Proveedor' },
  { value: 'TEMPERATURE', label: 'Temperatura' },
  { value: 'HAZMAT', label: 'Hazardous' },
]

const STATUS_LABELS: Record<QualityInspectionPlanStatus, string> = {
  DRAFT: 'Borrador',
  VALIDATED: 'Validado',
  SCHEDULED: 'Programado',
  ACTIVE: 'Activo',
  RETIRED: 'Retirado',
  ARCHIVED: 'Archivado',
}

const STATUS_TONE: Record<QualityInspectionPlanStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700',
  VALIDATED: 'bg-blue-50 text-blue-700',
  SCHEDULED: 'bg-amber-50 text-amber-700',
  ACTIVE: 'bg-emerald-50 text-emerald-700',
  RETIRED: 'bg-slate-100 text-slate-500',
  ARCHIVED: 'bg-slate-50 text-slate-400',
}

const PAGE_SIZE = 20

export function QualityInspectionPlansPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.procurementApprovals.policiesCreate)

  const [page, setPage] = useState(1)
  const [tab, setTab] = useState<TabKey>('all')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<QualityInspectionPlanStatus | ''>('')
  const [familyFilter, setFamilyFilter] = useState<QualityInspectionPlanFamily | ''>('')
  const [hasConflicts, setHasConflicts] = useState<boolean | undefined>(undefined)
  const [hasPackaging, setHasPackaging] = useState<boolean | undefined>(undefined)
  const [hasWeight, setHasWeight] = useState<boolean | undefined>(undefined)
  const [hasTemperature, setHasTemperature] = useState<boolean | undefined>(undefined)
  const [hasCertificates, setHasCertificates] = useState<boolean | undefined>(undefined)
  const [hasSampling, setHasSampling] = useState<boolean | undefined>(undefined)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search), 300)
    return () => window.clearTimeout(timer)
  }, [search])

  const query = useMemo<QualityPlanListQuery>(() => {
    const q: QualityPlanListQuery = { page, page_size: PAGE_SIZE }
    if (debouncedSearch) q.search = debouncedSearch
    if (tab === 'conflicts') {
      q.has_conflicts = true
    } else {
      const tabDef = TABS.find((t) => t.key === tab)
      if (tabDef?.status) q.status = tabDef.status
    }
    if (statusFilter) q.status = statusFilter
    if (familyFilter) q.family = familyFilter
    if (hasConflicts !== undefined) q.has_conflicts = hasConflicts
    if (hasPackaging !== undefined) q.has_packaging = hasPackaging
    if (hasWeight !== undefined) q.has_weight = hasWeight
    if (hasTemperature !== undefined) q.has_temperature = hasTemperature
    if (hasCertificates !== undefined) q.has_certificates = hasCertificates
    if (hasSampling !== undefined) q.has_sampling = hasSampling
    return q
  }, [page, debouncedSearch, tab, statusFilter, familyFilter, hasConflicts, hasPackaging, hasWeight, hasTemperature, hasCertificates, hasSampling])

  const plans = useQuery<PaginatedResponse<QualityInspectionPlan>>(
    ['quality-inspection-plans', 'list', JSON.stringify(query)],
    '/logistics/quality-inspection-plans',
    query as Record<string, unknown>,
  )

  const summary = useQuery<QualityInspectionPlanSummary>(
    ['quality-inspection-plans', 'summary'],
    '/logistics/quality-inspection-plans/summary',
  )

  useEffect(() => {
    setPage(1)
  }, [tab, debouncedSearch, statusFilter, familyFilter, hasConflicts, hasPackaging, hasWeight, hasTemperature, hasCertificates, hasSampling])

  const totalPages = Math.max(1, Math.ceil((plans.data?.total ?? 0) / PAGE_SIZE))

  const onTabChange = useCallback((key: TabKey) => {
    setTab(key)
  }, [])

  if (plans.isError) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Planes de inspección de calidad"
          actions={
            canCreate ? (
              <Button size="small" onClick={() => navigate('/logistics/quality-inspection-plans/new')}>
                Crear plan
              </Button>
            ) : undefined
          }
        />
        <Alert variant="error">{getErrorMessage(plans.error)}</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Fase 041"
        title="Planes de inspección de calidad"
        description="Gestión de planes, versiones, ámbitos, controles y conflictos."
        actions={
          canCreate ? (
            <Button size="small" onClick={() => navigate('/logistics/quality-inspection-plans/new')}>
              Crear plan
            </Button>
          ) : undefined
        }
      />

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <MetricCard label="Total planes" value={summary.data?.total_plans ?? 0} detail="Todos los estados" icon="document" tone="primary" />
        <MetricCard label="Activos" value={summary.data?.active_plans ?? 0} detail="En producción" icon="check" tone="success" />
        <MetricCard label="Borradores" value={summary.data?.draft_versions ?? 0} detail="Sin validar" icon="document" tone="neutral" />
        <MetricCard label="Programados" value={summary.data?.scheduled_versions ?? 0} detail="Pendientes activación" icon="calendar" tone="warning" />
        <MetricCard label="Con conflictos" value={summary.data?.plans_with_conflicts ?? 0} detail="Requieren resolución" icon="alert" tone="danger" />
        <MetricCard label="Vencen pronto" value={summary.data?.versions_expiring_soon ?? 0} detail="Próximos a vencer" icon="clock" tone="warning" />
      </div>

      {/* Tabs */}
      <nav className="flex gap-1 rounded-xl border border-[#EEF2F5] bg-slate-50 p-1 overflow-x-auto" aria-label="Filtrar por estado">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => onTabChange(t.key)}
            className={`whitespace-nowrap min-h-9 px-3 text-[11px] font-semibold rounded-lg transition-colors ${
              tab === t.key
                ? 'bg-white text-[#1F4E6D] shadow-sm'
                : 'text-slate-600 hover:bg-white/60'
            }`}
            aria-current={tab === t.key ? 'page' : undefined}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Search + Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1 min-w-0">
          <Input
            label="Buscar"
            placeholder="Código, nombre o descripción…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as QualityInspectionPlanStatus | '')}
            className="min-h-9 rounded-lg border border-[#DDE4E8] px-2 text-[11px] bg-white"
          >
            <option value="">Todos los estados</option>
            {(Object.keys(STATUS_LABELS) as QualityInspectionPlanStatus[]).map((s) => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </select>
          <select
            value={familyFilter}
            onChange={(e) => setFamilyFilter(e.target.value as QualityInspectionPlanFamily | '')}
            className="min-h-9 rounded-lg border border-[#DDE4E8] px-2 text-[11px] bg-white"
          >
            <option value="">Todas las familias</option>
            {FAMILY_OPTIONS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
          <label className="flex items-center gap-1.5 min-h-9 rounded-lg border border-[#DDE4E8] px-2 text-[11px] bg-white cursor-pointer">
            <input
              type="checkbox"
              checked={hasConflicts === true}
              onChange={(e) => setHasConflicts(e.target.checked ? true : undefined)}
              className="h-3.5 w-3.5 rounded border-slate-300"
            />
            Conflictos
          </label>
          <label className="flex items-center gap-1.5 min-h-9 rounded-lg border border-[#DDE4E8] px-2 text-[11px] bg-white cursor-pointer">
            <input
              type="checkbox"
              checked={hasPackaging === true}
              onChange={(e) => setHasPackaging(e.target.checked ? true : undefined)}
              className="h-3.5 w-3.5 rounded border-slate-300"
            />
            Embalaje
          </label>
          <label className="flex items-center gap-1.5 min-h-9 rounded-lg border border-[#DDE4E8] px-2 text-[11px] bg-white cursor-pointer">
            <input
              type="checkbox"
              checked={hasWeight === true}
              onChange={(e) => setHasWeight(e.target.checked ? true : undefined)}
              className="h-3.5 w-3.5 rounded border-slate-300"
            />
            Peso
          </label>
          <label className="flex items-center gap-1.5 min-h-9 rounded-lg border border-[#DDE4E8] px-2 text-[11px] bg-white cursor-pointer">
            <input
              type="checkbox"
              checked={hasTemperature === true}
              onChange={(e) => setHasTemperature(e.target.checked ? true : undefined)}
              className="h-3.5 w-3.5 rounded border-slate-300"
            />
            Temperatura
          </label>
          <label className="flex items-center gap-1.5 min-h-9 rounded-lg border border-[#DDE4E8] px-2 text-[11px] bg-white cursor-pointer">
            <input
              type="checkbox"
              checked={hasCertificates === true}
              onChange={(e) => setHasCertificates(e.target.checked ? true : undefined)}
              className="h-3.5 w-3.5 rounded border-slate-300"
            />
            Certificados
          </label>
          <label className="flex items-center gap-1.5 min-h-9 rounded-lg border border-[#DDE4E8] px-2 text-[11px] bg-white cursor-pointer">
            <input
              type="checkbox"
              checked={hasSampling === true}
              onChange={(e) => setHasSampling(e.target.checked ? true : undefined)}
              className="h-3.5 w-3.5 rounded border-slate-300"
            />
            Muestreo
          </label>
        </div>
      </div>

      {/* Table */}
      {plans.isLoading ? (
        <LoadingSkeleton rows={8} />
      ) : (plans.data?.items ?? []).length === 0 ? (
        <EmptyState
          title="Sin planes de inspección"
          description="No se encontraron planes con los filtros actuales."
          action={
            canCreate ? (
              <Button size="small" onClick={() => navigate('/logistics/quality-inspection-plans/new')}>
                Crear primer plan
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-[#EEF2F5]">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-[#EEF2F5] bg-slate-50 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  <th className="px-3 py-2">Código</th>
                  <th className="px-3 py-2">Nombre</th>
                  <th className="px-3 py-2">Familia</th>
                  <th className="px-3 py-2">Estado</th>
                  <th className="px-3 py-2 text-center">V. activa</th>
                  <th className="px-3 py-2 text-center">Prioridad</th>
                  <th className="px-3 py-2 text-center">Productos</th>
                  <th className="px-3 py-2 text-center">Categorías</th>
                  <th className="px-3 py-2 text-center">Controles</th>
                  <th className="px-3 py-2 text-center">Embalaje</th>
                  <th className="px-3 py-2 text-center">Peso</th>
                  <th className="px-3 py-2 text-center">Temp.</th>
                  <th className="px-3 py-2 text-center">Cert.</th>
                  <th className="px-3 py-2 text-center">Muest.</th>
                  <th className="px-3 py-2 text-center">Conflictos</th>
                  <th className="px-3 py-2">Actualización</th>
                  <th className="px-3 py-2 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF2F5]">
                {(plans.data?.items ?? []).map((plan) => (
                  <tr
                    key={plan.plan_id}
                    className="hover:bg-slate-50/60 cursor-pointer transition-colors"
                    onClick={() => navigate(`/logistics/quality-inspection-plans/${plan.plan_id}`)}
                  >
                    <td className="px-3 py-2 font-mono font-semibold text-[#1F4E6D]">{plan.code}</td>
                    <td className="px-3 py-2 max-w-[200px] truncate">{plan.name}</td>
                    <td className="px-3 py-2">{plan.family}</td>
                    <td className="px-3 py-2">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${STATUS_TONE[plan.status]}`}>
                        {STATUS_LABELS[plan.status]}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center font-mono">{plan.active_version_number ?? '—'}</td>
                    <td className="px-3 py-2 text-center">{String(plan.priority)}</td>
                    <td className="px-3 py-2 text-center">{String(plan.product_count)}</td>
                    <td className="px-3 py-2 text-center">{String(plan.category_count)}</td>
                    <td className="px-3 py-2 text-center">{String(plan.control_count)}</td>
                    <td className="px-3 py-2 text-center">{plan.has_packaging ? '✓' : '—'}</td>
                    <td className="px-3 py-2 text-center">{plan.has_weight ? '✓' : '—'}</td>
                    <td className="px-3 py-2 text-center">{plan.has_temperature ? '✓' : '—'}</td>
                    <td className="px-3 py-2 text-center">{plan.has_certificates ? '✓' : '—'}</td>
                    <td className="px-3 py-2 text-center">{plan.has_sampling ? '✓' : '—'}</td>
                    <td className="px-3 py-2 text-center">
                      {plan.conflict_count > 0 ? (
                        <span className="inline-block rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-bold text-red-700">
                          {String(plan.conflict_count)}
                        </span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-slate-500">
                      {plan.updated_at ? new Date(plan.updated_at).toLocaleDateString('es-PE') : '—'}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        size="small"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/logistics/quality-inspection-plans/${plan.plan_id}`)
                        }}
                      >
                        Ver
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            total={plans.data?.total ?? 0}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  )
}
