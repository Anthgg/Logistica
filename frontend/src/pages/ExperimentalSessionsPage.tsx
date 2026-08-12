import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { researchApi } from '../api/research-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useTranslations } from '../hooks/useTranslations'
import type { ExperimentalSession } from '../types/research'
import { formatDateTime } from '../utils/date'
import { getErrorMessage } from '../utils/errors'

export function ExperimentalSessionsPage() {
  const { translate } = useTranslations()
  const [sessions, setSessions] = useState<ExperimentalSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    setIsLoading(true)
    try { setSessions((await researchApi.listSessions()).items) }
    catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsLoading(false) }
  }, [])
  useEffect(() => { void load() }, [load])
  const columns: TableColumn<ExperimentalSession>[] = [
    { key: 'scenario', label: 'Escenario', render: (row) => <div className="table-primary"><Link className="table-link" to={`/research/sessions/${row.id}`}>{translate('common', row.scenario, row.scenario)}</Link><small>{row.id.slice(0, 8)}</small></div> },
    { key: 'status', label: 'Estado', render: (row) => <StatusBadge value={row.status} /> },
    { key: 'date', label: 'Inicio', render: (row) => formatDateTime(row.started_at) },
    { key: 'duration', label: 'Duración', render: (row) => row.duration_seconds === null ? 'En curso' : `${Math.round(row.duration_seconds / 60)} min` },
    { key: 'captures', label: 'Capturas / eventos', render: (row) => `${row.facial_capture_count} / ${row.keyboard_event_count + row.mouse_event_count}` },
    { key: 'action', label: '', align: 'right', render: (row) => <Link className="button button--ghost button--small" to={`/research/sessions/${row.id}`}>Ver resumen</Link> },
  ]
  return <div className="page"><PageHeader eyebrow="Auditoría experimental" title="Sesiones de investigación" description="Historial de sesiones, volúmenes capturados y errores del cliente." actions={<Button variant="secondary" onClick={() => void load()}>Actualizar</Button>} />{error && <Alert variant="error">{error}</Alert>}<section className="panel operations-section">{isLoading ? <div className="loading-panel"><span className="spinner" /><p>Cargando sesiones…</p></div> : <OperationsTable rows={sessions} columns={columns} getRowKey={(row) => row.id} />}</section></div>
}
