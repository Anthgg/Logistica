import { useCallback, useEffect, useMemo, useState } from 'react'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { ConfirmDialog } from '../components/common/ConfirmDialog'
import { Input } from '../components/common/Input'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { QueryBar } from '../components/common/QueryBar'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useAuth } from '../hooks/useAuth'
import type { Client, ClientCreate, PaginatedResponse } from '../types/operations'
import { getErrorMessage } from '../utils/errors'
import { permissionsFor } from '../utils/permissions'

const emptyForm: ClientCreate = {
  document_type: 'RUC',
  document_number: '',
  business_name: '',
  address: '',
  district: '',
  province: '',
  department: '',
  contact_name: '',
  contact_email: '',
  contact_phone: '',
}

export function ClientsPage() {
  const { user } = useAuth()
  const canManage = user ? permissionsFor(user.role).manageClients : false
  const { guardSensitiveAction } = useSensitiveOperationGuard()
  const [data, setData] = useState<PaginatedResponse<Client>>({ items: [], page: 1, page_size: 20, total: 0, total_pages: 0 })
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState<ClientCreate>(emptyForm)
  const [editing, setEditing] = useState<Client | null>(null)
  const [deleting, setDeleting] = useState<Client | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setData(await operationsApi.clients.list({ page, page_size: 20, search, sort_by: 'business_name' }))
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

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setIsOpen(true)
  }

  const openEdit = (client: Client) => {
    setEditing(client)
    setForm({
      document_type: client.document_type,
      document_number: client.document_number,
      business_name: client.business_name,
      address: client.address,
      district: client.district,
      province: client.province,
      department: client.department,
      contact_name: client.contact_name ?? '',
      contact_email: client.contact_email ?? '',
      contact_phone: client.contact_phone ?? '',
    })
    setIsOpen(true)
  }

  const save = async () => {
    setIsSaving(true)
    setError(null)
    try {
      if (editing) await operationsApi.clients.update(editing.id, form)
      else await operationsApi.clients.create(form)
      setSuccess(editing ? 'Cliente actualizado.' : 'Cliente creado.')
      setIsOpen(false)
      await load()
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  const remove = async () => {
    if (!deleting) return
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await operationsApi.clients.remove(deleting.id)
      })
      if (!executed) return
      setDeleting(null)
      setSuccess('Cliente eliminado.')
      await load()
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  const columns = useMemo<TableColumn<Client>[]>(() => [
    { key: 'name', label: 'Razón social', render: (row) => <div className="table-primary"><strong>{row.business_name}</strong><small>{row.document_type} {row.document_number}</small></div> },
    { key: 'location', label: 'Ubicación', render: (row) => `${row.district}, ${row.province}` },
    { key: 'contact', label: 'Contacto', render: (row) => row.contact_name ?? 'Sin contacto' },
    { key: 'status', label: 'Estado', render: (row) => <StatusBadge value={row.is_active ? 'active' : 'inactive'}>{row.is_active ? 'Activo' : 'Inactivo'}</StatusBadge> },
    { key: 'actions', label: 'Acciones', align: 'right', render: (row) => canManage && <div className="table-actions"><Button size="small" variant="ghost" onClick={() => openEdit(row)}>Editar</Button><Button size="small" variant="ghost" onClick={() => setDeleting(row)}>Eliminar</Button></div> },
  ], [canManage])

  const update = (key: keyof ClientCreate, value: string) => setForm((current) => ({ ...current, [key]: value }))

  return (
    <div className="page">
      <PageHeader eyebrow="Directorio comercial" title="Clientes" description="Empresas y destinatarios vinculados a la operación." actions={canManage ? <Button onClick={openCreate}>Nuevo cliente</Button> : undefined} />
      {error && <Alert variant="error" onDismiss={() => setError(null)}>{error}</Alert>}
      {success && <Alert variant="success" onDismiss={() => setSuccess(null)}>{success}</Alert>}
      <section className="panel operations-section">
        <QueryBar search={search} onSearch={(value) => { setSearch(value); setPage(1) }} />
        {isLoading ? <div className="loading-panel"><span className="spinner" /><p>Cargando clientes…</p></div> : <OperationsTable rows={data.items} columns={columns} getRowKey={(row) => row.id} />}
        <Pagination page={data.page} totalPages={data.total_pages} total={data.total} onPageChange={setPage} />
      </section>
      <ResourceDialog isOpen={isOpen} title={editing ? 'Editar cliente' : 'Nuevo cliente'} submitLabel={editing ? 'Guardar cambios' : 'Crear cliente'} isSubmitting={isSaving} onClose={() => setIsOpen(false)} onSubmit={() => void save()}>
        <div className="form-grid">
          <Input label="Tipo de documento" value={form.document_type} onChange={(e) => update('document_type', e.target.value)} required />
          <Input label="Número de documento" value={form.document_number} onChange={(e) => update('document_number', e.target.value)} minLength={4} required />
          <Input className="form-grid__full" label="Razón social" value={form.business_name} onChange={(e) => update('business_name', e.target.value)} required />
          <Input className="form-grid__full" label="Dirección" value={form.address} onChange={(e) => update('address', e.target.value)} required />
          <Input label="Distrito" value={form.district} onChange={(e) => update('district', e.target.value)} required />
          <Input label="Provincia" value={form.province} onChange={(e) => update('province', e.target.value)} required />
          <Input label="Departamento" value={form.department} onChange={(e) => update('department', e.target.value)} required />
          <Input label="Contacto" value={form.contact_name ?? ''} onChange={(e) => update('contact_name', e.target.value)} />
          <Input label="Correo" type="email" value={form.contact_email ?? ''} onChange={(e) => update('contact_email', e.target.value)} />
          <Input label="Teléfono" value={form.contact_phone ?? ''} onChange={(e) => update('contact_phone', e.target.value)} />
        </div>
      </ResourceDialog>
      <ConfirmDialog isOpen={deleting !== null} title="¿Eliminar cliente?" description={`Se eliminará ${deleting?.business_name ?? 'este cliente'}.`} confirmLabel="Eliminar" isLoading={isSaving} onCancel={() => setDeleting(null)} onConfirm={() => void remove()} />
    </div>
  )
}
