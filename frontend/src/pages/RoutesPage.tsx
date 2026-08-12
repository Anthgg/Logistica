import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { SelectField } from '../components/common/FormControls'
import { Input } from '../components/common/Input'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { QueryBar } from '../components/common/QueryBar'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import { useAuth } from '../hooks/useAuth'
import type { DeliveryRoute, RouteCreate, RouteStatus } from '../types/operations'
import { getErrorMessage } from '../utils/errors'
import { permissionsFor } from '../utils/permissions'

const emptyForm: RouteCreate = { route_code: '', name: '', origin: '', destination: '', scheduled_date: '', driver_name: '', vehicle_plate: '', status: 'planned' }
const statuses: RouteStatus[] = ['planned', 'active', 'completed', 'cancelled']

export function RoutesPage() {
  const { user } = useAuth()
  const canManage = user ? permissionsFor(user.role).manageRoutes : false
  const [routes, setRoutes] = useState<DeliveryRoute[]>([])
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [form, setForm] = useState<RouteCreate>(emptyForm)
  const [editing, setEditing] = useState<DeliveryRoute | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try { setRoutes((await operationsApi.routes.list({ page_size: 100, search, status, sort_by: 'scheduled_date', sort_order: 'desc' })).items) }
    catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsLoading(false) }
  }, [search, status])

  useEffect(() => { const timer = window.setTimeout(() => void load(), 250); return () => window.clearTimeout(timer) }, [load])

  const open = (route?: DeliveryRoute) => {
    setEditing(route ?? null)
    setForm(route ? {
      route_code: route.route_code, name: route.name, origin: route.origin, destination: route.destination,
      scheduled_date: route.scheduled_date, driver_name: route.driver_name ?? '', vehicle_plate: route.vehicle_plate ?? '', status: route.status,
    } : emptyForm)
    setIsOpen(true)
  }
  const save = async () => {
    setIsSaving(true)
    try {
      if (editing) {
        const { route_code: _routeCode, ...body } = form
        await operationsApi.routes.update(editing.id, body)
      } else await operationsApi.routes.create(form)
      setIsOpen(false); await load()
    } catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsSaving(false) }
  }

  const columns = useMemo<TableColumn<DeliveryRoute>[]>(() => [
    { key: 'route', label: 'Ruta', render: (row) => <div className="table-primary"><Link className="table-link" to={`/routes/${row.id}`}>{row.name}</Link><small>{row.route_code}</small></div> },
    { key: 'journey', label: 'Recorrido', render: (row) => `${row.origin} → ${row.destination}` },
    { key: 'date', label: 'Fecha', render: (row) => new Intl.DateTimeFormat('es-PE').format(new Date(`${row.scheduled_date}T12:00:00`)) },
    { key: 'driver', label: 'Conductor / unidad', render: (row) => <div className="table-primary"><span>{row.driver_name ?? 'Sin asignar'}</span><small>{row.vehicle_plate ?? 'Sin placa'}</small></div> },
    { key: 'status', label: 'Estado', render: (row) => <StatusBadge value={row.status} /> },
    { key: 'actions', label: '', align: 'right', render: (row) => <div className="table-actions">{canManage && <Button variant="ghost" size="small" onClick={() => open(row)}>Editar</Button>}<Link className="button button--ghost button--small" to={`/routes/${row.id}`}>Gestionar</Link></div> },
  ], [canManage])
  const update = (key: keyof RouteCreate, value: string) => setForm((current) => ({ ...current, [key]: value }))

  return <div className="page">
    <PageHeader eyebrow="Planificación de reparto" title="Rutas" description="Programación de recorridos, conductores y carga asignada." actions={canManage ? <Button onClick={() => open()}>Nueva ruta</Button> : undefined} />
    {error && <Alert variant="error">{error}</Alert>}
    <section className="panel operations-section">
      <QueryBar search={search} onSearch={setSearch}><SelectField label="Estado" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Todos</option>{statuses.map((item) => <option key={item} value={item}>{item}</option>)}</SelectField></QueryBar>
      {isLoading ? <div className="loading-panel"><span className="spinner" /><p>Cargando rutas…</p></div> : <OperationsTable rows={routes} columns={columns} getRowKey={(row) => row.id} />}
    </section>
    <ResourceDialog isOpen={isOpen} title={editing ? 'Editar ruta' : 'Nueva ruta'} submitLabel={editing ? 'Guardar cambios' : 'Crear ruta'} isSubmitting={isSaving} onClose={() => setIsOpen(false)} onSubmit={() => void save()}>
      <div className="form-grid">
        <Input label="Código" value={form.route_code} onChange={(e) => update('route_code', e.target.value)} disabled={Boolean(editing)} required />
        <Input label="Nombre" value={form.name} onChange={(e) => update('name', e.target.value)} required />
        <Input label="Origen" value={form.origin} onChange={(e) => update('origin', e.target.value)} required />
        <Input label="Destino" value={form.destination} onChange={(e) => update('destination', e.target.value)} required />
        <Input label="Fecha programada" type="date" value={form.scheduled_date} onChange={(e) => update('scheduled_date', e.target.value)} required />
        <SelectField label="Estado" value={form.status} onChange={(e) => update('status', e.target.value)}>{statuses.map((item) => <option key={item} value={item}>{item}</option>)}</SelectField>
        <Input label="Conductor" value={form.driver_name ?? ''} onChange={(e) => update('driver_name', e.target.value)} />
        <Input label="Placa del vehículo" value={form.vehicle_plate ?? ''} onChange={(e) => update('vehicle_plate', e.target.value.toUpperCase())} />
      </div>
    </ResourceDialog>
  </div>
}
