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
import type { PaginatedResponse, RoleResponse } from '../types/logistics-resources'
import { getErrorMessage } from '../utils/errors'

export function RolesPage() {
  const access = useLogisticsAccess()
  const canReadPermissions = access.hasPermission(
    LOGISTICS_PERMISSIONS.rolePermissions.read,
  )

  const [data, setData] = useState<PaginatedResponse<RoleResponse>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await logisticsApi.roles.list({ page, page_size: 20, search })
      // Normaliza: el backend puede devolver un array o { items: [...] }
      const normalized: PaginatedResponse<RoleResponse> = Array.isArray(res)
        ? { items: res, page, page_size: 20, total: res.length, total_pages: 1 }
        : { items: res.items ?? [], page: res.page ?? page, page_size: res.page_size ?? 20, total: res.total ?? 0, total_pages: res.total_pages ?? 0 }
      setData(normalized)
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [page, search])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250)
    return () => window.clearTimeout(timer)
  }, [load])

  const columns: TableColumn<RoleResponse>[] = [
    {
      key: 'name',
      label: 'Rol',
      render: (row) => (
        <div className="table-primary">
          <strong>{row.name}</strong>
          <small>{row.code}</small>
        </div>
      ),
    },
    {
      key: 'description',
      label: 'Descripción',
      render: (row) => row.description,
    },
    {
      key: 'role_type',
      label: 'Tipo',
      render: (row) => row.role_type,
    },
    {
      key: 'is_system',
      label: 'Sistema',
      render: (row) =>
        row.is_system ? (
          <StatusBadge value="active">Sistema</StatusBadge>
        ) : (
          <StatusBadge value="inactive">Personalizado</StatusBadge>
        ),
    },
    {
      key: 'status',
      label: 'Estado',
      render: (row) => (
        <StatusBadge value={row.status === 'active' ? 'active' : 'inactive'}>
          {row.status === 'active' ? 'Activo' : 'Inactivo'}
        </StatusBadge>
      ),
    },
  ]

  return (
    <div className="page">
      <PageHeader
        eyebrow="Control de acceso"
        title="Roles logísticos"
        description="Consulta el catálogo de roles logísticos. Los roles de sistema son administrados centralmente."
      />
      {error && <Alert variant="error">{error}</Alert>}
      <section className="panel operations-section">
        <QueryBar
          search={search}
          onSearch={(value) => {
            setSearch(value)
            setPage(1)
          }}
        />
        {isLoading ? (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Cargando roles…</p>
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
      {!canReadPermissions && (
        <p className="text-xs text-slate-500 mt-2">
          Los permisos detallados por rol requieren el permiso{' '}
          <code>logistics.role_permissions.read</code>.
        </p>
      )}
    </div>
  )
}