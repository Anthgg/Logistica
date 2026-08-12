import { useCallback, useEffect, useState } from 'react'
import { logisticsApi } from '../api/logistics-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { QueryBar } from '../components/common/QueryBar'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import { PermissionGate } from '../components/logistics/PermissionGate'
import { useLogisticsAccess } from '../features/logistics-me/hooks/useLogisticsAccess'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type {
  OrganizationResponse,
  OrganizationCreate,
  PaginatedResponse,
} from '../types/logistics-resources'
import { getErrorMessage } from '../utils/errors'

const emptyForm: OrganizationCreate = {
  code: '',
  name: '',
  country_code: 'PE',
  timezone: 'America/Lima',
}

export function OrganizationsPage() {
  const access = useLogisticsAccess()
  const canCreate = access.hasPermission(LOGISTICS_PERMISSIONS.organizations.create)
  const canUpdate = access.hasPermission(LOGISTICS_PERMISSIONS.organizations.update)
  const canChangeStatus = access.hasPermission(
    LOGISTICS_PERMISSIONS.organizations.changeStatus,
  )
  const canManage = canCreate || canUpdate || canChangeStatus

  const [data, setData] = useState<PaginatedResponse<OrganizationResponse>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState<OrganizationCreate>(emptyForm)
  const [editing, setEditing] = useState<OrganizationResponse | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setData(await logisticsApi.organizations.list({ page, page_size: 20, search }))
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

  const openEdit = (org?: OrganizationResponse) => {
    setEditing(org ?? null)
    setForm(
      org
        ? {
            code: org.code,
            name: org.name,
            country_code: org.country_code,
            timezone: org.timezone,
          }
        : emptyForm,
    )
    setIsOpen(true)
  }

  const save = async () => {
    setIsSaving(true)
    try {
      if (editing) {
        await logisticsApi.organizations.update(editing.id, {
          name: form.name,
          country_code: form.country_code,
          timezone: form.timezone,
        })
      } else {
        await logisticsApi.organizations.create(form)
      }
      setIsOpen(false)
      await load()
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  const toggleStatus = async (org: OrganizationResponse) => {
    setIsSaving(true)
    try {
      await logisticsApi.organizations.changeStatus(editing?.id ?? org.id, {
        status: org.status === 'active' ? 'inactive' : 'active',
      })
      await load()
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  const columns: TableColumn<OrganizationResponse>[] = [
    {
      key: 'name',
      label: 'Organización',
      render: (row) => (
        <div className="table-primary">
          <strong>{row.name}</strong>
          <small>{row.code}</small>
        </div>
      ),
    },
    {
      key: 'country_code',
      label: 'País',
      render: (row) => row.country_code,
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
            {canUpdate && (
              <Button size="small" variant="ghost" onClick={() => openEdit(row)}>
                Editar
              </Button>
            )}
            {canChangeStatus && (
              <Button
                size="small"
                variant="ghost"
                onClick={() => void toggleStatus(row)}
              >
                {row.status === 'active' ? 'Desactivar' : 'Activar'}
              </Button>
            )}
          </div>
        ),
    },
  ]

  const updateText = (key: keyof OrganizationCreate, value: string) =>
    setForm((current) => ({ ...current, [key]: value }))

  return (
    <div className="page">
      <PageHeader
        eyebrow="Estructura organizacional"
        title="Organizaciones"
        description="Gestiona las organizaciones de la red logística."
        actions={
          <PermissionGate permission={LOGISTICS_PERMISSIONS.organizations.create}>
            <Button onClick={() => openEdit()}>Nueva organización</Button>
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
            <p>Cargando organizaciones…</p>
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
      <ResourceDialog
        isOpen={isOpen}
        title={editing ? 'Editar organización' : 'Nueva organización'}
        submitLabel={editing ? 'Guardar cambios' : 'Crear organización'}
        isSubmitting={isSaving}
        onClose={() => setIsOpen(false)}
        onSubmit={() => void save()}
      >
        <div className="form-grid">
          <Input
            label="Código"
            value={form.code}
            onChange={(e) => updateText('code', e.target.value)}
            required
            disabled={Boolean(editing)}
          />
          <Input
            label="Nombre"
            value={form.name}
            onChange={(e) => updateText('name', e.target.value)}
            required
          />
          <Input
            label="Código de país"
            value={form.country_code}
            onChange={(e) => updateText('country_code', e.target.value)}
            required
          />
          <Input
            label="Zona horaria"
            value={form.timezone}
            onChange={(e) => updateText('timezone', e.target.value)}
            required
          />
        </div>
      </ResourceDialog>
    </div>
  )
}