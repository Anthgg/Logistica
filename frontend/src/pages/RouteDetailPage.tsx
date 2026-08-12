import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import { useAuth } from '../hooks/useAuth'
import type { DeliveryRoute, Shipment } from '../types/operations'
import { getErrorMessage } from '../utils/errors'
import { permissionsFor } from '../utils/permissions'

export function RouteDetailPage() {
  const { routeId = '' } = useParams()
  const { user } = useAuth()
  const canManage = user ? permissionsFor(user.role).manageRoutes : false
  const [route, setRoute] = useState<DeliveryRoute | null>(null)
  const [assigned, setAssigned] = useState<Shipment[]>([])
  const [available, setAvailable] = useState<Shipment[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [detail, assignedPage, availablePage] = await Promise.all([
        operationsApi.routes.get(routeId),
        operationsApi.shipments.list({ route_id: routeId, page_size: 100 }),
        operationsApi.shipments.list({ status: 'registered', page_size: 100 }),
      ])
      setRoute(detail); setAssigned(assignedPage.items); setAvailable(availablePage.items)
    } catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsLoading(false) }
  }, [routeId])
  useEffect(() => { void load() }, [load])

  const assign = async () => {
    if (!selected.size) return
    setIsSaving(true)
    try { await operationsApi.routes.assign(routeId, [...selected]); setSelected(new Set()); setIsOpen(false); await load() }
    catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsSaving(false) }
  }
  const unassign = async (shipmentId: string) => {
    setIsSaving(true)
    try { await operationsApi.routes.unassign(routeId, shipmentId); await load() }
    catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsSaving(false) }
  }
  const columns: TableColumn<Shipment>[] = [
    { key: 'code', label: 'Código', render: (row) => <Link className="table-link" to={`/shipments/${row.id}`}>{row.tracking_code}</Link> },
    { key: 'route', label: 'Destino', render: (row) => `${row.destination_district} · ${row.destination_address}` },
    { key: 'priority', label: 'Prioridad', render: (row) => <StatusBadge value={row.priority} /> },
    { key: 'action', label: '', align: 'right', render: (row) => canManage && <Button size="small" variant="ghost" disabled={isSaving} onClick={() => void unassign(row.id)}>Retirar</Button> },
  ]
  return <div className="page">
    <div className="back-link"><Link to="/routes">← Volver a rutas</Link></div>
    <PageHeader eyebrow="Detalle de ruta" title={route?.name ?? 'Ruta'} description={route ? `${route.origin} → ${route.destination}` : 'Gestión de carga asignada.'} actions={canManage ? <Button onClick={() => setIsOpen(true)}>Asignar envíos</Button> : undefined} />
    {error && <Alert variant="error">{error}</Alert>}
    {isLoading ? <div className="panel loading-panel"><span className="spinner" /><p>Cargando ruta…</p></div> : route && <><section className="route-summary"><div><span>Código</span><strong>{route.route_code}</strong></div><div><span>Fecha</span><strong>{route.scheduled_date}</strong></div><div><span>Conductor</span><strong>{route.driver_name ?? 'Sin asignar'}</strong></div><div><span>Estado</span><StatusBadge value={route.status} /></div></section><section className="panel operations-section"><div className="section-heading"><div><p className="eyebrow">Carga</p><h2>Envíos asignados</h2></div></div><OperationsTable rows={assigned} columns={columns} getRowKey={(row) => row.id} emptyMessage="Esta ruta todavía no tiene envíos." /></section></>}
    <ResourceDialog isOpen={isOpen} title="Asignar envíos" description="Selecciona envíos registrados y aún disponibles." submitLabel={`Asignar ${selected.size || ''}`} isSubmitting={isSaving} onClose={() => setIsOpen(false)} onSubmit={() => void assign()}>
      <div className="selection-list">{available.map((shipment) => <label key={shipment.id}><input type="checkbox" checked={selected.has(shipment.id)} onChange={(event) => setSelected((current) => { const next = new Set(current); if (event.target.checked) next.add(shipment.id); else next.delete(shipment.id); return next })} /><span><strong>{shipment.tracking_code}</strong><small>{shipment.destination_district} · {shipment.package_description}</small></span></label>)}{available.length === 0 && <p className="muted">No hay envíos disponibles.</p>}</div>
    </ResourceDialog>
  </div>
}
