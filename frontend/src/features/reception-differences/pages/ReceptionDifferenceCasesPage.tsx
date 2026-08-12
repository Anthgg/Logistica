import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  ReceptionDifferenceCase,
  ReceptionDifferenceCaseStatus,
  ReceptionDifferenceSeverity,
} from '../types/reception-differences'

const STATUS_TABS: { value: ReceptionDifferenceCaseStatus | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'Todos' },
  { value: 'DRAFT', label: 'Borradores' },
  { value: 'EVIDENCE_PENDING', label: 'Evidencia pendiente' },
  { value: 'RESPONSIBILITY_PENDING', label: 'Responsabilidad pendiente' },
  { value: 'IN_REVIEW', label: 'En revisión' },
  { value: 'CHANGES_REQUESTED', label: 'Cambios solicitados' },
  { value: 'PENDING_APPROVAL', label: 'Pendientes de aprobación' },
  { value: 'ISSUED', label: 'Emitidos' },
  { value: 'ACKNOWLEDGED', label: 'Reconocidos' },
  { value: 'DISPUTED', label: 'Disputados' },
  { value: 'FOLLOW_UP', label: 'Seguimiento' },
  { value: 'CLOSED', label: 'Cerrados' },
  { value: 'CANCELLED', label: 'Cancelados' },
]

const SEVERITY_COLORS: Record<ReceptionDifferenceSeverity, string> = {
  LOW: 'bg-slate-100 text-slate-700',
  MEDIUM: 'bg-amber-100 text-amber-700',
  HIGH: 'bg-orange-100 text-orange-700',
  CRITICAL: 'bg-rose-100 text-rose-700',
}

const STATUS_COLORS: Record<ReceptionDifferenceCaseStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700',
  EVIDENCE_PENDING: 'bg-amber-100 text-amber-700',
  RESPONSIBILITY_PENDING: 'bg-amber-100 text-amber-700',
  IN_REVIEW: 'bg-blue-100 text-blue-700',
  CHANGES_REQUESTED: 'bg-orange-100 text-orange-700',
  PENDING_APPROVAL: 'bg-purple-100 text-purple-700',
  ISSUED: 'bg-emerald-100 text-emerald-700',
  ACKNOWLEDGED: 'bg-emerald-100 text-emerald-700',
  DISPUTED: 'bg-rose-100 text-rose-700',
  FOLLOW_UP: 'bg-blue-100 text-blue-700',
  CLOSED: 'bg-slate-100 text-slate-500',
  CANCELLED: 'bg-slate-100 text-slate-400',
}

const STATUS_LABELS: Record<ReceptionDifferenceCaseStatus, string> = {
  DRAFT: 'Borrador',
  EVIDENCE_PENDING: 'Evidencia pendiente',
  RESPONSIBILITY_PENDING: 'Responsabilidad pendiente',
  IN_REVIEW: 'En revisión',
  CHANGES_REQUESTED: 'Cambios solicitados',
  PENDING_APPROVAL: 'Pendiente de aprobación',
  ISSUED: 'Emitido',
  ACKNOWLEDGED: 'Reconocido',
  DISPUTED: 'Disputado',
  FOLLOW_UP: 'Seguimiento',
  CLOSED: 'Cerrado',
  CANCELLED: 'Cancelado',
}

export function ReceptionDifferenceCasesPage() {
  const auth = useLogisticsPermissions()
  const [activeTab, setActiveTab] = useState<ReceptionDifferenceCaseStatus | 'ALL'>('ALL')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timer)
  }, [search])

  const query = useMemo(() => ({
    ...(activeTab !== 'ALL' ? { status: activeTab } : {}),
    ...(debouncedSearch ? { search: debouncedSearch } : {}),
    page: 1,
    page_size: 50,
  }), [activeTab, debouncedSearch])

  const casesQuery = useQuery<{ items: ReceptionDifferenceCase[]; total: number }>(
    ['reception-differences', query],
    '/logistics/reception-difference-cases',
    query,
  )

  const canCreate = auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.create)

  if (!auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.view)) {
    return (
      <div className="page">
        <div className="panel p-6 text-center text-sm text-slate-500">
          No tienes permisos para ver las diferencias de recepción.
        </div>
      </div>
    )
  }

  const cases = casesQuery.data?.items ?? []
  const total = casesQuery.data?.total ?? 0
  const visibleOpenCases = cases.filter((item) => !['CLOSED', 'CANCELLED'].includes(item.status)).length
  const visibleCriticalCases = cases.filter((item) => item.severity === 'CRITICAL').length

  return (
    <div className="page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-800">Diferencias de Recepción</h1>
          <p className="text-xs text-slate-500">{total} caso{total !== 1 ? 's' : ''}</p>
        </div>
        {canCreate && (
          <Link
            to="/logistics/inbound/reception-differences/new"
            className="rounded-lg bg-[#1F4E6D] px-4 py-2 text-sm font-semibold text-white hover:bg-[#173a55]"
          >
            Crear caso
          </Link>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryCard label="Total encontrado" value={total} />
        <SummaryCard label="Casos visibles" value={cases.length} />
        <SummaryCard label="Abiertos visibles" value={visibleOpenCases} />
        <SummaryCard label="Críticos visibles" value={visibleCriticalCases} tone="rose" />
      </div>

      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Buscar por código DIF, recepción, OC, proveedor, SKU…"
        className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm"
        aria-label="Buscar casos de diferencia"
      />

      <div className="flex flex-wrap gap-1.5" role="tablist">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              activeTab === tab.value
                ? 'bg-[#1F4E6D] text-white'
                : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {casesQuery.isLoading ? (
        <div className="panel p-8 text-center text-sm text-slate-400">Cargando…</div>
      ) : cases.length === 0 ? (
        <div className="panel p-8 text-center text-sm text-slate-400">
          No se encontraron casos de diferencia.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="px-3 py-2 font-semibold">Código</th>
                <th className="px-3 py-2 font-semibold">Recepción</th>
                <th className="px-3 py-2 font-semibold">Proveedor</th>
                <th className="px-3 py-2 font-semibold">Almacén</th>
                <th className="px-3 py-2 font-semibold">Estado</th>
                <th className="px-3 py-2 font-semibold">Severidad</th>
                <th className="px-3 py-2 font-semibold">Ítems</th>
                <th className="px-3 py-2 font-semibold">Evidencias</th>
                <th className="px-3 py-2 font-semibold">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.case_id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono font-semibold text-slate-800">
                    {c.case_code ?? '—'}
                  </td>
                  <td className="px-3 py-2 text-slate-600">{c.receipt_code}</td>
                  <td className="px-3 py-2 text-slate-600">{c.supplier_name}</td>
                  <td className="px-3 py-2 text-slate-600">{c.warehouse_name}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-bold ${STATUS_COLORS[c.status]}`}>
                      {STATUS_LABELS[c.status]}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-bold ${SEVERITY_COLORS[c.severity]}`}>
                      {c.severity}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-600">{c.items_count}</td>
                  <td className="px-3 py-2 text-slate-600">{c.evidence_count}</td>
                  <td className="px-3 py-2">
                    <Link
                      to={`/logistics/inbound/reception-differences/${c.case_id}`}
                      className="font-semibold text-[#1F4E6D] hover:underline"
                    >
                      Ver detalle
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function SummaryCard({ label, value, tone = 'slate' }: { label: string; value: number; tone?: string }) {
  const colorMap: Record<string, string> = {
    slate: 'text-slate-800',
    rose: 'text-rose-600',
    amber: 'text-amber-600',
    emerald: 'text-emerald-600',
  }
  return (
    <div className="panel p-3">
      <p className="text-[10px] font-semibold uppercase text-slate-400">{label}</p>
      <p className={`text-xl font-bold ${colorMap[tone] ?? 'text-slate-800'}`}>{value}</p>
    </div>
  )
}
