import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { purchaseRequisitionsApi } from '../api/purchase-requisitions-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import {
  RequisitionPriorityBadge,
  RequisitionStatusBadge,
} from '../components/purchase-requisitions/RequisitionStatusBadge'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type { PaginatedResponse } from '../types/logistics-resources'
import type {
  PurchaseRequisitionListQuery,
  PurchaseRequisitionPriority,
  PurchaseRequisitionStatus,
  PurchaseRequisitionStats,
  PurchaseRequisitionSummary,
} from '../types/purchase-requisitions'

const PAGE_SIZE = 20

export function PurchaseRequisitionsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'all'

  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.purchaseRequisitions.create)

  const [data, setData] = useState<PaginatedResponse<PurchaseRequisitionSummary> | null>(null)
  const [stats, setStats] = useState<PurchaseRequisitionStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)

  // Filters
  const [status, setStatus] = useState<PurchaseRequisitionStatus | ''>('')
  const [priority, setPriority] = useState<PurchaseRequisitionPriority | ''>('')

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 400)
    return () => clearTimeout(timer)
  }, [search])

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const query: PurchaseRequisitionListQuery = {
        page,
        page_size: PAGE_SIZE,
        search: debouncedSearch || undefined,
        status: status || undefined,
        priority: priority || undefined,
        mine_only: tab === 'mine',
        pending_my_review: tab === 'review',
      }
      const [res, statsRes] = await Promise.all([
        purchaseRequisitionsApi.list(query),
        purchaseRequisitionsApi.getStats().catch(() => null),
      ])
      setData(res)
      if (statsRes) setStats(statsRes)
    } finally {
      setLoading(false)
    }
  }, [page, debouncedSearch, status, priority, tab])

  useEffect(() => {
    void loadData()
  }, [loadData])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Requerimientos de Compra (REQ)"
        description="Elaboración, revisión y aprobación de solicitudes internas de materiales y mercaderías."
        actions={
          canCreate ? (
            <Button onClick={() => navigate('/logistics/purchasing/requisitions/new')}>
              + Nuevo Requerimiento
            </Button>
          ) : undefined
        }
      />

      {/* Summary Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6 text-xs">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Total REQ</span>
            <span className="font-mono text-xl font-bold text-slate-800">{stats.total_requisitions}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Borradores</span>
            <span className="font-mono text-xl font-bold text-slate-600">{stats.draft_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">En Revisión</span>
            <span className="font-mono text-xl font-bold text-indigo-700">{stats.under_review_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Aprobados</span>
            <span className="font-mono text-xl font-bold text-emerald-700">{stats.approved_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Devueltos</span>
            <span className="font-mono text-xl font-bold text-amber-700">{stats.returned_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Urgentes</span>
            <span className="font-mono text-xl font-bold text-rose-600">{stats.urgent_count}</span>
          </div>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="border-b border-slate-200 text-xs">
        <nav className="flex gap-4">
          {[
            { id: 'all', label: 'Todos los Requerimientos' },
            { id: 'mine', label: 'Mis Solicitudes' },
            { id: 'review', label: `Bandeja de Revisión (${stats?.pending_my_review_count || 0})` },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                setSearchParams({ tab: t.id })
                setPage(1)
              }}
              className={`pb-3 font-bold border-b-2 transition-colors ${
                tab === t.id
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs text-xs">
        <div className="flex flex-1 flex-wrap items-center gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por código REQ, solicitante, centro de costo o producto..."
            className="w-full sm:w-80 rounded-xl border border-slate-300 px-3.5 py-2 font-medium placeholder:text-slate-400"
          />

          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as PurchaseRequisitionStatus | '')
              setPage(1)
            }}
            className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
          >
            <option value="">Todos los estados</option>
            <option value="DRAFT">Borrador</option>
            <option value="SUBMITTED">Enviado</option>
            <option value="UNDER_REVIEW">En Revisión</option>
            <option value="RETURNED">Devuelto</option>
            <option value="APPROVED">Aprobado</option>
            <option value="REJECTED">Rechazado</option>
          </select>

          <select
            value={priority}
            onChange={(e) => {
              setPriority(e.target.value as PurchaseRequisitionPriority | '')
              setPage(1)
            }}
            className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
          >
            <option value="">Todas las prioridades</option>
            <option value="LOW">Baja</option>
            <option value="NORMAL">Normal</option>
            <option value="HIGH">Alta</option>
            <option value="URGENT">Urgente</option>
            <option value="CRITICAL">Crítica</option>
          </select>
        </div>

        {(search || status || priority) && (
          <button
            type="button"
            onClick={() => {
              setSearch('')
              setStatus('')
              setPriority('')
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
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500 text-xs">
          No se encontraron requerimientos de compra registrados.
        </div>
      ) : (
        <div className="space-y-4 text-xs">
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Código REQ</th>
                  <th className="px-4 py-3 text-left font-semibold">Solicitante / Centro Costo</th>
                  <th className="px-4 py-3 text-center font-semibold">Prioridad</th>
                  <th className="px-4 py-3 text-left font-semibold">Fecha Requerida</th>
                  <th className="px-4 py-3 text-left font-semibold">Productos Resumidos</th>
                  <th className="px-4 py-3 text-center font-semibold">Líneas</th>
                  <th className="px-4 py-3 text-center font-semibold">Estado</th>
                  <th className="px-4 py-3 text-right font-semibold">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {data.items.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => navigate(`/logistics/purchasing/requisitions/${row.id}`)}
                    className="cursor-pointer hover:bg-slate-50/80 transition-colors"
                  >
                    <td className="px-4 py-3 font-mono font-bold text-indigo-700 text-sm">
                      {row.requisition_code}
                      <span className="text-slate-400 block text-[10px] font-normal font-sans">v{row.active_revision_number}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-800">
                      <span className="font-bold block">{row.cost_center_name}</span>
                      <span className="text-[10px] text-slate-400">{row.applicant_user_name}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <RequisitionPriorityBadge priority={row.priority} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-slate-700 font-mono">
                      {new Date(row.required_date).toLocaleDateString('es-PE')}
                    </td>
                    <td className="px-4 py-3 text-slate-600 font-medium">
                      {row.products_summary || 'Sin productos'}
                    </td>
                    <td className="px-4 py-3 text-center font-mono font-bold">
                      {row.lines_count}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <RequisitionStatusBadge status={row.status} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/logistics/purchasing/requisitions/${row.id}`)
                        }}
                        className="font-semibold text-indigo-600 hover:underline"
                      >
                        Ver Detalle →
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
