import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { businessPartnersApi } from '../api/business-partners-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { QueryBar } from '../components/common/QueryBar'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import type { PaginatedResponse } from '../types/logistics-resources'
import type { BusinessPartner, BusinessPartnerCreate, BusinessPartnerRoleType } from '../types/business-partners'
import { getErrorMessage } from '../utils/errors'

export function BusinessPartnersPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<BusinessPartner>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState<BusinessPartnerCreate>({
    legal_name: '',
    trade_name: '',
    tax_id: '',
    country_code: 'PE',
    roles: ['SUPPLIER'],
  })

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setData(await businessPartnersApi.list({ page, page_size: 20, search }))
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [page, search])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250)
    return () => window.clearTimeout(timer)
  }, [load])

  const handleCreate = async () => {
    setIsSaving(true)
    try {
      await businessPartnersApi.create(form)
      setIsCreateOpen(false)
      await load()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const toggleRole = (role: BusinessPartnerRoleType) => {
    setForm((c) => {
      const exists = c.roles.includes(role)
      return {
        ...c,
        roles: exists ? c.roles.filter((r) => r !== role) : [...c.roles, role],
      }
    })
  }

  const columns = useMemo<TableColumn<BusinessPartner>[]>(
    () => [
      {
        key: 'legal_name',
        label: 'Razón Social / Código',
        render: (row) => (
          <div className="table-primary">
            <strong>{row.legal_name}</strong>
            <small className="font-mono text-slate-500">{row.tax_id} ({row.code})</small>
          </div>
        ),
      },
      {
        key: 'roles',
        label: 'Roles Asignados',
        render: (row) => (
          <div className="flex gap-1 flex-wrap">
            {row.roles.map((r) => (
              <span key={r} className="font-mono text-[10px] bg-blue-100 text-blue-900 px-1.5 py-0.5 rounded font-bold">
                {r}
              </span>
            ))}
          </div>
        ),
      },
      {
        key: 'risk',
        label: 'Nivel de Riesgo',
        render: (row) => (
          <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded font-bold text-slate-700">
            {row.risk_level}
          </span>
        ),
      },
      {
        key: 'compliance',
        label: 'Cumplimiento',
        render: (row) => row.compliance_status,
      },
      {
        key: 'status',
        label: 'Estado',
        render: (row) => (
          <StatusBadge value={row.status.toLowerCase()}>{row.status}</StatusBadge>
        ),
      },
      {
        key: 'actions',
        label: 'Acciones',
        align: 'right',
        render: (row) => (
          <Button
            size="small"
            variant="ghost"
            onClick={() => navigate(`/logistics/business-partners/${row.id}`)}
          >
            Expediente
          </Button>
        ),
      },
    ],
    [navigate],
  )

  return (
    <div className="page">
      <PageHeader
        eyebrow="Maestro unificado de la cadena de suministro"
        title="Socios de Negocio"
        description="Gestión integral de proveedores, clientes y transportistas sin duplicidad de entidades."
        actions={<Button onClick={() => setIsCreateOpen(true)}>Nuevo Socio</Button>}
      />

      {error && <Alert variant="error">{error}</Alert>}

      <section className="panel operations-section space-y-3">
        <QueryBar
          search={search}
          onSearch={(val) => {
            setSearch(val)
            setPage(1)
          }}
        />

        {isLoading ? (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Cargando maestro unificado de socios de negocio…</p>
          </div>
        ) : (
          <OperationsTable rows={data.items} columns={columns} getRowKey={(row) => row.id} />
        )}

        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          total={data.total}
          onPageChange={setPage}
        />
      </section>

      <ResourceDialog
        isOpen={isCreateOpen}
        title="Registrar nuevo socio de negocio"
        submitLabel="Crear socio"
        isSubmitting={isSaving}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={() => void handleCreate()}
      >
        <div className="space-y-3 text-xs">
          <Input
            label="Razón Social Oficial"
            value={form.legal_name}
            onChange={(e) => setForm((c) => ({ ...c, legal_name: e.target.value }))}
            required
          />
          <Input
            label="Nombre Comercial"
            value={form.trade_name}
            onChange={(e) => setForm((c) => ({ ...c, trade_name: e.target.value }))}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="RUC / Identificador Fiscal (Decimal String)"
              value={form.tax_id}
              onChange={(e) => setForm((c) => ({ ...c, tax_id: e.target.value }))}
              required
            />
            <Input
              label="Código País (ISO 3166-1)"
              value={form.country_code}
              onChange={(e) => setForm((c) => ({ ...c, country_code: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="font-semibold text-slate-700 block mb-1">Roles Asignados (Un solo registro común)</label>
            <div className="flex gap-4 pt-1">
              {(['SUPPLIER', 'CUSTOMER', 'CARRIER'] as BusinessPartnerRoleType[]).map((r) => (
                <label key={r} className="flex items-center gap-1.5 cursor-pointer font-bold text-slate-700">
                  <input
                    type="checkbox"
                    checked={form.roles.includes(r)}
                    onChange={() => toggleRole(r)}
                  />
                  {r}
                </label>
              ))}
            </div>
          </div>
        </div>
      </ResourceDialog>
    </div>
  )
}
