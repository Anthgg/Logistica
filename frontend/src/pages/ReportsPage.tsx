import { useCallback, useEffect, useState } from 'react'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useTranslations } from '../hooks/useTranslations'
import type { TranslationNamespace } from '../types/i18n'
import type { CountGroup, DateCount, LowStockRow, RouteSummaryRow } from '../types/operations'
import { getErrorMessage } from '../utils/errors'

interface ReportData {
  byStatus: CountGroup[]
  byPriority: CountGroup[]
  deliveries: DateCount[]
  incidents: CountGroup[]
  lowStock: LowStockRow[]
  routes: RouteSummaryRow[]
}
const empty: ReportData = { byStatus: [], byPriority: [], deliveries: [], incidents: [], lowStock: [], routes: [] }

export function ReportsPage() {
  const { translate } = useTranslations()
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [data, setData] = useState<ReportData>(empty)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    const query = { date_from: dateFrom || undefined, date_to: dateTo || undefined }
    try {
      const [byStatus, byPriority, deliveries, incidents, lowStock, routes] = await Promise.all([
        operationsApi.reports.count('shipments-by-status', query),
        operationsApi.reports.count('shipments-by-priority', query),
        operationsApi.reports.deliveries(query),
        operationsApi.reports.count('incidents-summary', query),
        operationsApi.reports.lowStock(),
        operationsApi.reports.routes(query),
      ])
      setData({ byStatus, byPriority, deliveries, incidents, lowStock, routes })
    } catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsLoading(false) }
  }, [dateFrom, dateTo])
  useEffect(() => { void load() }, [load])

  const lowStockColumns: TableColumn<LowStockRow>[] = [
    { key: 'sku', label: 'SKU', render: (row) => row.sku },
    { key: 'name', label: 'Artículo', render: (row) => row.name },
    { key: 'stock', label: 'Existencia', render: (row) => row.current_stock },
    { key: 'min', label: 'Mínimo', render: (row) => row.minimum_stock },
    { key: 'state', label: '', render: () => <StatusBadge value="high">Reponer</StatusBadge> },
  ]
  const routeColumns: TableColumn<RouteSummaryRow>[] = [
    { key: 'code', label: 'Ruta', render: (row) => row.route_code },
    { key: 'status', label: 'Estado', render: (row) => <StatusBadge value={row.status} /> },
    { key: 'shipments', label: 'Envíos', render: (row) => row.shipment_count },
  ]

  return <div className="page">
    <PageHeader eyebrow="Inteligencia operativa" title="Reportes" description="Indicadores calculados por el backend, sin datos simulados." actions={<Button variant="secondary" onClick={() => void load()} disabled={isLoading}>Actualizar</Button>} />
    {error && <Alert variant="error">{error}</Alert>}
    <section className="report-filters panel"><Input label="Desde" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} /><Input label="Hasta" type="date" value={dateTo} min={dateFrom} onChange={(e) => setDateTo(e.target.value)} /></section>
    {isLoading ? <div className="panel loading-panel"><span className="spinner" /><p>Calculando reportes…</p></div> : <>
      <div className="report-grid">
        <BarChart title="Envíos por estado" items={data.byStatus} namespace="status" translate={translate} />
        <BarChart title="Envíos por prioridad" items={data.byPriority} namespace="priority" translate={translate} />
        <BarChart title="Incidencias" items={data.incidents} namespace="common" translate={translate} />
        <DateChart items={data.deliveries} />
      </div>
      <div className="operations-grid">
        <section className="panel operations-section"><div className="section-heading"><div><p className="eyebrow">Excepciones</p><h2>Stock bajo</h2></div></div><OperationsTable rows={data.lowStock} columns={lowStockColumns} getRowKey={(row) => row.id} /></section>
        <section className="panel operations-section"><div className="section-heading"><div><p className="eyebrow">Capacidad de reparto</p><h2>Resumen de rutas</h2></div></div><OperationsTable rows={data.routes} columns={routeColumns} getRowKey={(row) => row.route_id} /></section>
      </div>
    </>}
  </div>
}

function BarChart({
  title,
  items,
  namespace,
  translate,
}: {
  title: string
  items: CountGroup[]
  namespace: TranslationNamespace
  translate: (namespace: TranslationNamespace, key: string, fallback?: string) => string
}) {
  const max = Math.max(...items.map((item) => item.count), 1)
  return <section className="panel chart-card"><p className="eyebrow">Distribución</p><h2>{title}</h2><div className="bar-chart">{items.map((item) => <div key={item.key} className="bar-chart__row"><div><span>{translate(namespace, item.key, item.key)}</span><strong>{item.count}</strong></div><div className="bar-chart__track"><span style={{ width: `${(item.count / max) * 100}%` }} /></div></div>)}{items.length === 0 && <p className="muted">Sin datos para el periodo.</p>}</div></section>
}
function DateChart({ items }: { items: DateCount[] }) {
  const max = Math.max(...items.map((item) => item.count), 1)
  return <section className="panel chart-card"><p className="eyebrow">Serie temporal</p><h2>Entregas por fecha</h2><div className="column-chart">{items.slice(-14).map((item) => <div key={item.date} title={`${item.date}: ${item.count}`}><span style={{ height: `${Math.max((item.count / max) * 100, 4)}%` }} /><small>{item.date.slice(5)}</small></div>)}</div>{items.length === 0 && <p className="muted">Sin entregas en el periodo.</p>}</section>
}
