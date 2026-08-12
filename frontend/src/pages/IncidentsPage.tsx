import { useCallback, useEffect, useMemo, useState } from 'react'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { SelectField, TextareaField } from '../components/common/FormControls'
import { Input } from '../components/common/Input'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { QueryBar } from '../components/common/QueryBar'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useAuth } from '../hooks/useAuth'
import { useTranslations } from '../hooks/useTranslations'
import type { Incident, IncidentCreate, IncidentSeverity, IncidentStatus, IncidentType } from '../types/operations'
import { formatDateTime } from '../utils/date'
import { getErrorMessage } from '../utils/errors'
import { permissionsFor } from '../utils/permissions'

const types: IncidentType[] = ['delay', 'damaged_package', 'missing_package', 'incorrect_address', 'failed_delivery', 'vehicle_problem', 'inventory_difference', 'other']
const severities: IncidentSeverity[] = ['low', 'medium', 'high', 'critical']
const incidentStatuses: IncidentStatus[] = ['open', 'investigating', 'resolved', 'closed']
const emptyForm: IncidentCreate = { shipment_id: null, incident_type: 'delay', title: '', description: '', severity: 'medium', assigned_to: null }

export function IncidentsPage() {
  const { user } = useAuth()
  const { translate } = useTranslations()
  const permissions = user ? permissionsFor(user.role) : permissionsFor('')
  const { guardSensitiveAction } = useSensitiveOperationGuard()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [form, setForm] = useState<IncidentCreate>(emptyForm)
  const [resolving, setResolving] = useState<Incident | null>(null)
  const [resolution, setResolution] = useState('')
  const [dialog, setDialog] = useState<'create' | 'resolve' | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    try { setIncidents((await operationsApi.incidents.list({ page_size: 100, search, status, sort_by: 'created_at', sort_order: 'desc' })).items) }
    catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsLoading(false) }
  }, [search, status])
  useEffect(() => { const timer = window.setTimeout(() => void load(), 250); return () => window.clearTimeout(timer) }, [load])

  const create = async () => {
    setIsSaving(true)
    try { await operationsApi.incidents.create(form); setForm(emptyForm); setDialog(null); await load() }
    catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsSaving(false) }
  }
  const resolve = async () => {
    if (!resolving) return
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await operationsApi.incidents.resolve(resolving.id, resolution)
      })
      if (!executed) return
      setResolving(null)
      setResolution('')
      setDialog(null)
      await load()
    }
    catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsSaving(false) }
  }

  const columns = useMemo<TableColumn<Incident>[]>(() => [
    { key: 'incident', label: 'Incidencia', render: (row) => <div className="table-primary"><strong>{row.title}</strong><small>{translate('event', row.incident_type, row.incident_type)}</small></div> },
    { key: 'severity', label: 'Severidad', render: (row) => <StatusBadge value={row.severity} namespace="risk" /> },
    { key: 'status', label: 'Estado', render: (row) => <StatusBadge value={row.status} /> },
    { key: 'date', label: 'Registro', render: (row) => formatDateTime(row.created_at) },
    { key: 'actions', label: '', align: 'right', render: (row) => permissions.resolveIncidents && !['resolved', 'closed'].includes(row.status) && <Button size="small" variant="secondary" onClick={() => { setResolving(row); setDialog('resolve') }}>Resolver</Button> },
  ], [permissions.resolveIncidents, translate])

  return <div className="page">
    <PageHeader eyebrow="Gestión de excepciones" title="Incidencias" description="Seguimiento de problemas operativos y sus resoluciones." actions={permissions.manageIncidents ? <Button onClick={() => setDialog('create')}>Reportar incidencia</Button> : undefined} />
    {error && <Alert variant="error">{error}</Alert>}
    <section className="panel operations-section"><QueryBar search={search} onSearch={setSearch}><SelectField label="Estado" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Todos</option>{incidentStatuses.map((item) => <option key={item} value={item}>{translate('status', item, item)}</option>)}</SelectField></QueryBar>{isLoading ? <div className="loading-panel"><span className="spinner" /><p>Cargando incidencias…</p></div> : <OperationsTable rows={incidents} columns={columns} getRowKey={(row) => row.id} />}</section>
    <ResourceDialog isOpen={dialog === 'create'} title="Reportar incidencia" submitLabel="Registrar incidencia" isSubmitting={isSaving} onClose={() => setDialog(null)} onSubmit={() => void create()}>
      <div className="form-grid"><SelectField label="Tipo" value={form.incident_type} onChange={(e) => setForm((current) => ({ ...current, incident_type: e.target.value as IncidentType }))}>{types.map((item) => <option key={item} value={item}>{translate('event', item, item)}</option>)}</SelectField><SelectField label="Severidad" value={form.severity} onChange={(e) => setForm((current) => ({ ...current, severity: e.target.value as IncidentSeverity }))}>{severities.map((item) => <option key={item} value={item}>{translate('risk', item, item)}</option>)}</SelectField><Input className="form-grid__full" label="Título" value={form.title} onChange={(e) => setForm((current) => ({ ...current, title: e.target.value }))} required /><Input className="form-grid__full" label="ID de envío (opcional)" value={form.shipment_id ?? ''} onChange={(e) => setForm((current) => ({ ...current, shipment_id: e.target.value || null }))} /><TextareaField className="form-grid__full" label="Descripción" value={form.description} onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))} required /></div>
    </ResourceDialog>
    <ResourceDialog isOpen={dialog === 'resolve'} title={`Resolver ${resolving?.title ?? 'incidencia'}`} submitLabel="Marcar como resuelta" isSubmitting={isSaving} onClose={() => setDialog(null)} onSubmit={() => void resolve()}><TextareaField label="Resolución aplicada" value={resolution} onChange={(e) => setResolution(e.target.value)} minLength={3} required /></ResourceDialog>
  </div>
}
