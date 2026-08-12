import { useCallback, useEffect, useState } from 'react'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { DashboardHeading, RefreshButton } from '../components/dashboard/DashboardHeading'
import { OperationsSummary } from '../components/dashboard/OperationsSummary'
import { KpiGrid } from '../components/dashboard/KpiGrid'
import { RecentShipmentsTable } from '../components/dashboard/RecentShipmentsTable'
import { StatusDistribution } from '../components/dashboard/StatusDistribution'
import { RecentActivity } from '../components/dashboard/RecentActivity'
import type { DashboardSummary } from '../types/operations'
import { getErrorMessage } from '../utils/errors'
import { useTranslations } from '../hooks/useTranslations'

export function DashboardPage() {
  const { catalogVersion } = useTranslations()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    // Dashboard activity labels are localized by the backend.
    void catalogVersion
    setIsLoading(true)
    setError(null)
    try {
      setSummary(await operationsApi.dashboard())
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [catalogVersion])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="flex flex-col gap-4 w-full min-w-0">
      {/* Encabezado */}
      <DashboardHeading
        eyebrow="CENTRO DE CONTROL"
        title="Pulso logístico"
        description="Lectura consolidada de despachos, rutas, incidencias e inventario."
        actions={<RefreshButton onClick={() => void load()} disabled={isLoading} />}
      />

      {error && (
        <Alert variant="error" title="No pudimos sincronizar el centro de control">
          {error}
        </Alert>
      )}

      {isLoading ? (
        <LoadingSkeleton label="Consultando la operación logística…" rows={6} />
      ) : summary ? (
        <>
          {/* Resumen operativo */}
          <OperationsSummary
            totalShipments={summary.total_shipments}
            inTransit={summary.in_transit_shipments}
            pendingShipments={summary.pending_shipments}
            deliveriesToday={summary.deliveries_today}
            criticalIncidents={summary.critical_incidents}
            deliveredShipments={summary.delivered_shipments}
            routesToday={summary.routes_today}
          />

          {/* Tarjetas KPI */}
          <KpiGrid summary={summary} />

          {/* Área principal: Grid distribuido en 2 columnas fluidas con min-w-0 */}
          <div className="grid w-full min-w-0 grid-cols-1 items-start gap-4 xl:grid-cols-[minmax(0,1fr)_320px] 2xl:grid-cols-[minmax(0,1fr)_360px]">
            {/* Columna izquierda: Tabla principal que crece con el contenedor */}
            <section className="w-full min-w-0">
              <RecentShipmentsTable shipments={summary.recent_shipments} />
            </section>

            {/* Columna derecha: Panel lateral con ancho controlado */}
            <aside className="w-full min-w-0 flex flex-col gap-4">
              <StatusDistribution
                statusMap={summary.shipments_by_status}
                total={summary.total_shipments}
              />
              <RecentActivity activities={summary.recent_activity} />
            </aside>
          </div>
        </>
      ) : null}
    </div>
  )
}
