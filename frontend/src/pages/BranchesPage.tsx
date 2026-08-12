import { useCallback, useEffect, useState } from 'react'
import { logisticsApi } from '../api/logistics-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { QueryBar } from '../components/common/QueryBar'
import { StatusBadge } from '../components/common/StatusBadge'
import { PermissionGate } from '../components/logistics/PermissionGate'
import { useLogisticsAccess } from '../features/logistics-me/hooks/useLogisticsAccess'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type {
  BranchResponse,
  OrganizationResponse,
  PaginatedResponse,
} from '../types/logistics-resources'
import { getErrorMessage } from '../utils/errors'

export function BranchesPage() {
  const access = useLogisticsAccess()
  const canCreate = access.hasPermission(LOGISTICS_PERMISSIONS.branches.create)
  const canUpdate = access.hasPermission(LOGISTICS_PERMISSIONS.branches.update)
  const canChangeStatus = access.hasPermission(
    LOGISTICS_PERMISSIONS.branches.changeStatus,
  )
  const canManage = canCreate || canUpdate || canChangeStatus

  const [orgs, setOrgs] = useState<OrganizationResponse[]>([])
  const [selectedOrg, setSelectedOrg] = useState<string>('')
  const [data, setData] = useState<PaginatedResponse<BranchResponse>>({
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

  useEffect(() => {
    void logisticsApi.organizations
      .list({ page: 1, page_size: 100 })
      .then((res: PaginatedResponse<OrganizationResponse>) => {
        setOrgs(res.items)
        if (res.items.length > 0 && !selectedOrg) {
          setSelectedOrg(res.items[0].id)
        }
      })
      .catch(() => undefined)
  }, [selectedOrg])

  const load = useCallback(async () => {
    if (!selectedOrg) {
      setIsLoading(false)
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      setData(
        await logisticsApi.organizations.branches(selectedOrg, {
          page,
          page_size: 20,
          search,
        }),
      )
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [selectedOrg, page, search])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250)
    return () => window.clearTimeout(timer)
  }, [load])

  const toggleStatus = async (branch: BranchResponse) => {
    try {
      await logisticsApi.branches.changeStatus(branch.id, {
        status: branch.status === 'active' ? 'inactive' : 'active',
      })
      await load()
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    }
  }

  const columns: TableColumn<BranchResponse>[] = [
    {
      key: 'name',
      label: 'Sede',
      render: (row) => (
        <div className="table-primary">
          <strong>{row.name}</strong>
          <small>{row.code}</small>
        </div>
      ),
    },
    {
      key: 'address_text',
      label: 'Dirección',
      render: (row) => row.address_text ?? 'No definida',
    },
    {
      key: 'timezone',
      label: 'Zona horaria',
      render: (row) => row.timezone,
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
    {
      key: 'actions',
      label: 'Acciones',
      align: 'right',
      render: (row) =>
        canManage && (
          <div className="table-actions">
            {canChangeStatus && (
              <Button size="small" variant="ghost" onClick={() => void toggleStatus(row)}>
                {row.status === 'active' ? 'Desactivar' : 'Activar'}
              </Button>
            )}
          </div>
        ),
    },
  ]

  return (
    <div className="page">
      <PageHeader
        eyebrow="Estructura organizacional"
        title="Sedes"
        description="Gestiona las sedes por organización."
        actions={
          <PermissionGate permission={LOGISTICS_PERMISSIONS.branches.create}>
            <Button disabled={!selectedOrg}>Nueva sede</Button>
          </PermissionGate>
        }
      />
      {error && <Alert variant="error">{error}</Alert>}
      <section className="panel operations-section">
        <div className="flex items-center gap-3 mb-4">
          <label htmlFor="org-select" className="text-sm font-medium text-slate-700">
            Organización:
          </label>
          <select
            id="org-select"
            className="field__input"
            value={selectedOrg}
            onChange={(e) => {
              setSelectedOrg(e.target.value)
              setPage(1)
            }}
            disabled={isLoading}
          >
            <option value="">Selecciona una organización</option>
            {orgs.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name} ({org.code})
              </option>
            ))}
          </select>
        </div>
        {selectedOrg ? (
          <>
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
                <p>Cargando sedes…</p>
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
          </>
        ) : (
          <div className="loading-panel">
            <p>Selecciona una organización para ver sus sedes.</p>
          </div>
        )}
      </section>
    </div>
  )
}