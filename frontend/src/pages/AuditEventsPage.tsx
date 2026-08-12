import { useCallback, useEffect, useState } from 'react'
import { logisticsApi } from '../api/logistics-api'
import { Alert } from '../components/common/Alert'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { QueryBar } from '../components/common/QueryBar'
import { StatusBadge } from '../components/common/StatusBadge'
import { useLogisticsAccess } from '../features/logistics-me/hooks/useLogisticsAccess'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type {
  AuditEventListQuery,
  AuditEventSummaryResponse,
  PaginatedResponse,
} from '../types/logistics-resources'
import { getErrorMessage } from '../utils/errors'

export function AuditEventsPage() {
  const access = useLogisticsAccess()
  const [data, setData] = useState<PaginatedResponse<AuditEventSummaryResponse>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const query: AuditEventListQuery = { page, page_size: 20, search }
      if (severityFilter) query.severity = severityFilter
      setData(await logisticsApi.auditEvents.list(query))
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [page, search, severityFilter])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250)
    return () => window.clearTimeout(timer)
  }, [load])

  const columns: TableColumn<AuditEventSummaryResponse>[] = [
    {
      key: 'occurred_at',
      label: 'Fecha',
      render: (row) => new Date(row.occurred_at).toLocaleString('es-PE'),
    },
    {
      key: 'event_code',
      label: 'Código',
      render: (row) => <code className="text-xs">{row.event_code}</code>,
    },
    {
      key: 'event_category',
      label: 'Categoría',
      render: (row) => row.event_category,
    },
    {
      key: 'actor_display_name_snapshot',
      label: 'Actor',
      render: (row) => row.actor_display_name_snapshot ?? 'Sistema',
    },
    {
      key: 'action',
      label: 'Acción',
      render: (row) => row.action ?? '—',
    },
    {
      key: 'result',
      label: 'Resultado',
      render: (row) => (
        <StatusBadge value={row.result === 'success' ? 'active' : 'inactive'}>
          {row.result}
        </StatusBadge>
      ),
    },
    {
      key: 'severity',
      label: 'Severidad',
      render: (row) => (
        <StatusBadge value={row.severity === 'low' ? 'active' : 'inactive'}>
          {row.severity}
        </StatusBadge>
      ),
    },
    {
      key: 'resource_type',
      label: 'Recurso',
      render: (row) => row.resource_type ?? '—',
    },
  ]

  if (!access.hasPermission(LOGISTICS_PERMISSIONS.audit.read)) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Auditoría"
          title="Eventos de auditoría"
          description="Registro de eventos del sistema logístico."
        />
        <Alert variant="error">No tienes permisos para ver eventos de auditoría.</Alert>
      </div>
    )
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Auditoría"
        title="Eventos de auditoría"
        description="Registro de eventos del sistema logístico."
      />
      {error && <Alert variant="error">{error}</Alert>}
      <section className="panel operations-section">
        <div className="flex items-center gap-3 mb-4">
          <QueryBar
            search={search}
            onSearch={(value) => {
              setSearch(value)
              setPage(1)
            }}
          />
          <select
            className="field__input max-w-[160px]"
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value)
              setPage(1)
            }}
            aria-label="Filtrar por severidad"
          >
            <option value="">Todas las severidades</option>
            <option value="low">Baja</option>
            <option value="medium">Media</option>
            <option value="high">Alta</option>
            <option value="critical">Crítica</option>
          </select>
        </div>
        {isLoading ? (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Cargando eventos…</p>
          </div>
        ) : (
          <OperationsTable
            rows={data.items}
            columns={columns}
            getRowKey={(row) => row.id}
          />
        )}
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          total={data.total}
          onPageChange={setPage}
        />
      </section>
    </div>
  )
}