import { useCallback, useEffect, useState } from 'react'
import { logisticsApi } from '../api/logistics-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { QueryBar } from '../components/common/QueryBar'
import { StatusBadge } from '../components/common/StatusBadge'
import { ActionReasonDialog } from '../components/logistics/ActionReasonDialog'
import { PermissionGate } from '../components/logistics/PermissionGate'
import { useLogisticsAccess } from '../features/logistics-me/hooks/useLogisticsAccess'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type {
  PaginatedResponse,
  RoleAssignmentResponse,
} from '../types/logistics-resources'
import { getErrorMessage } from '../utils/errors'

export function RoleAssignmentsPage() {
  const access = useLogisticsAccess()
  const canRevoke = access.hasPermission(LOGISTICS_PERMISSIONS.roleAssignments.revoke)
  const [data, setData] = useState<PaginatedResponse<RoleAssignmentResponse>>({
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
  const [revoking, setRevoking] = useState<RoleAssignmentResponse | null>(null)
  const [isRevoking, setIsRevoking] = useState(false)
  const [revokeError, setRevokeError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setData(await logisticsApi.roleAssignments.list({ page, page_size: 20, search }))
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

  const confirmRevoke = async (reason: string) => {
    if (!revoking) return
    setIsRevoking(true)
    setRevokeError(null)
    try {
      await logisticsApi.roleAssignments.revoke(revoking.id, { reason })
      setRevoking(null)
      await load()
    } catch (caught: unknown) {
      setRevokeError(getErrorMessage(caught))
    } finally {
      setIsRevoking(false)
    }
  }

  const columns: TableColumn<RoleAssignmentResponse>[] = [
    {
      key: 'user_id',
      label: 'Usuario',
      render: (row) => <span className="font-mono text-xs">{row.user_id.slice(0, 8)}</span>,
    },
    {
      key: 'role_id',
      label: 'Rol',
      render: (row) => <span className="font-mono text-xs">{row.role_id.slice(0, 8)}</span>,
    },
    {
      key: 'scope_type',
      label: 'Alcance',
      render: (row) => row.scope_type,
    },
    {
      key: 'status',
      label: 'Estado',
      render: (row) => (
        <StatusBadge value={row.status === 'active' ? 'active' : 'inactive'}>
          {row.status === 'active' ? 'Activo' : row.status}
        </StatusBadge>
      ),
    },
    {
      key: 'ends_at',
      label: 'Expira',
      render: (row) =>
        row.ends_at
          ? new Date(row.ends_at).toLocaleDateString('es-PE')
          : 'Sin expiración',
    },
    {
      key: 'actions',
      label: 'Acciones',
      align: 'right',
      render: (row) =>
        canRevoke && row.status === 'active' ? (
          <Button
            size="small"
            variant="ghost"
            onClick={() => {
              setRevoking(row)
              setRevokeError(null)
            }}
          >
            Revocar
          </Button>
        ) : null,
    },
  ]

  return (
    <div className="page">
      <PageHeader
        eyebrow="Control de acceso"
        title="Asignaciones de roles"
        description="Gestiona las asignaciones de roles a usuarios con sus alcances."
        actions={
          <PermissionGate permission={LOGISTICS_PERMISSIONS.roleAssignments.create}>
            <Button>Nueva asignación</Button>
          </PermissionGate>
        }
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
            <p>Cargando asignaciones…</p>
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
      <ActionReasonDialog
        isOpen={revoking !== null}
        title="Revocar asignación de rol"
        resourceLabel={`Asignación: ${revoking?.id.slice(0, 8) ?? ''}`}
        consequence="El usuario perderá el rol y sus permisos asociados inmediatamente."
        confirmLabel="Revocar"
        isLoading={isRevoking}
        errorMessage={revokeError}
        onConfirm={(reason) => void confirmRevoke(reason)}
        onCancel={() => {
          setRevoking(null)
          setRevokeError(null)
        }}
      />
    </div>
  )
}