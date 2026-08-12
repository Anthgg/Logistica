import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { driversApi } from '../api/drivers-api'
import { PageHeader } from '../components/common/PageHeader'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { EmptyState } from '../components/common/EmptyState'
import { Pagination } from '../components/common/Pagination'
import { Alert } from '../components/common/Alert'
import { getErrorMessage } from '../utils/errors'
import type { DriverAlert, DriverAlertListQuery, DriverAlertSeverity, DriverAlertStatus, DriverAlertType } from '../types/drivers'
import type { PaginatedResponse } from '../types/logistics-resources'

const TYPE_LABELS: Record<DriverAlertType, string> = {
  LICENSE_EXPIRED: 'Licencia vencida',
  LICENSE_EXPIRING_SOON: 'Licencia por vencer',
  CATEGORY_EXPIRING_SOON: 'Categoría por vencer',
  DOCUMENT_EXPIRED: 'Documento vencido',
  DOCUMENT_MISSING: 'Documento faltante',
  CARRIER_EXPIRING_SOON: 'Transportista por vencer',
  RESTRICTION_ACTIVE: 'Restricción activa',
  PHOTO_PENDING: 'Foto pendiente',
  REVIEW_REQUIRED: 'Revisión requerida',
}

const SEVERITY_LABELS: Record<DriverAlertSeverity, string> = {
  INFO: 'Info',
  WARNING: 'Advertencia',
  CRITICAL: 'Crítica',
}

const SEVERITY_STYLES: Record<DriverAlertSeverity, string> = {
  INFO: 'bg-blue-50 text-blue-700 border-blue-300',
  WARNING: 'bg-amber-50 text-amber-700 border-amber-300',
  CRITICAL: 'bg-rose-50 text-rose-700 border-rose-300',
}

const STATUS_LABELS: Record<DriverAlertStatus, string> = {
  OPEN: 'Abierta',
  ACKNOWLEDGED: 'Reconocida',
  RESOLVED: 'Resuelta',
  DISMISSED: 'Descartada',
}

export function DriverAlertsPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<DriverAlert>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [typeFilter, setTypeFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const query: DriverAlertListQuery = {
        page,
        page_size: 20,
        type: (typeFilter || undefined) as DriverAlertType | undefined,
        severity: (severityFilter || undefined) as DriverAlertSeverity | undefined,
        status: (statusFilter || undefined) as DriverAlertStatus | undefined,
      }
      const res = await driversApi.listAlerts(query)
      setData(res)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [page, typeFilter, severityFilter, statusFilter])

  useEffect(() => {
    void load()
  }, [load])

  const clearFilters = () => {
    setTypeFilter('')
    setSeverityFilter('')
    setStatusFilter('')
    setPage(1)
  }

  const hasFilters = Boolean(typeFilter || severityFilter || statusFilter)

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader title="Alertas de conductores" description="Vencimientos, documentos faltantes y restricciones activas" />

      <div className="flex flex-wrap gap-2">
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="">Todos los tipos</option>
          {Object.entries(TYPE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select value={severityFilter} onChange={(e) => { setSeverityFilter(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="">Severidad</option>
          {Object.entries(SEVERITY_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="">Estado</option>
          {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        {hasFilters && <Button variant="ghost" onClick={clearFilters}>Limpiar</Button>}
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : data.items.length === 0 ? (
        <EmptyState title="Sin alertas" description="No hay alertas activas con los filtros aplicados." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Conductor</th>
                <th className="px-3 py-2">Tipo</th>
                <th className="px-3 py-2 hidden sm:table-cell">Severidad</th>
                <th className="px-3 py-2">Vencimiento</th>
                <th className="px-3 py-2 hidden md:table-cell">Días restantes</th>
                <th className="px-3 py-2 hidden lg:table-cell">Transportista</th>
                <th className="px-3 py-2">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((alert) => (
                <tr
                  key={alert.id}
                  onClick={() => navigate(`/logistics/drivers/${alert.driver_id}`)}
                  className="cursor-pointer hover:bg-slate-50"
                >
                  <td className="px-3 py-2">
                    <div className="font-medium text-slate-900">{alert.driver_name}</div>
                    <div className="text-xs text-slate-500">{alert.driver_code}</div>
                  </td>
                  <td className="px-3 py-2 text-slate-700">{TYPE_LABELS[alert.type] ?? alert.type}</td>
                  <td className="px-3 py-2 hidden sm:table-cell">
                    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${SEVERITY_STYLES[alert.severity]}`}>
                      {SEVERITY_LABELS[alert.severity]}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-600">{alert.expiration_date ?? '—'}</td>
                  <td className="px-3 py-2 hidden md:table-cell text-slate-600">{alert.days_remaining ?? '—'}</td>
                  <td className="px-3 py-2 hidden lg:table-cell text-slate-600">{alert.carrier_partner_name ?? '—'}</td>
                  <td className="px-3 py-2">
                    <span className={`text-xs ${alert.status === 'OPEN' ? 'text-amber-600' : alert.status === 'RESOLVED' ? 'text-emerald-600' : 'text-slate-400'}`}>
                      {STATUS_LABELS[alert.status]}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && data.total > 0 && (
        <Pagination page={data.page} totalPages={data.total_pages} total={data.total} onPageChange={setPage} />
      )}
    </div>
  )
}