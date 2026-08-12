import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import type { InventoryBalanceAlert } from '../types/inventory-balances'

const severityColors: Record<string, string> = {
  CRITICAL: 'border-rose-200 bg-rose-50 text-rose-700',
  HIGH: 'border-amber-200 bg-amber-50 text-amber-700',
  MEDIUM: 'border-blue-200 bg-blue-50 text-blue-700',
  LOW: 'border-slate-200 bg-slate-50 text-slate-600',
}

const typeLabels: Record<string, string> = {
  NEGATIVE_BALANCE: 'Saldo negativo',
  PROJECTION_LAG: 'Lag de proyección',
  SEQUENCE_GAP: 'Gap de secuencia',
  HASH_MISMATCH: 'Hash no coincide',
  RECONCILIATION_MISMATCH: 'Reconciliación fallida',
  UNIT_CONFLICT: 'Conflicto de unidad',
  POSITION_CONFLICT: 'Conflicto de posición',
  BASELINE_MISSING: 'Baseline faltante',
  REBUILD_REQUIRED: 'Rebuild requerido',
}

export function InventoryBalanceAlertsPage() {
  const { currentContext } = useLogisticsAccess()
  const organizationId = currentContext?.organization_id

  const alerts = useQuery<InventoryBalanceAlert[]>(
    ['inventory-balances', 'alerts', organizationId ?? ''],
    '/logistics/inventory/balances/alerts',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: Boolean(organizationId) },
  )

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Alertas de saldo"
        description="Incidencias técnicas detectadas en la proyección de saldos."
      />

      {alerts.isLoading && <LoadingSkeleton rows={6} />}
      {alerts.isError && <Alert variant="error">{getErrorMessage(alerts.error)}</Alert>}

      {alerts.data && alerts.data.length === 0 && (
        <Alert variant="info">No hay alertas activas.</Alert>
      )}

      {alerts.data && alerts.data.length > 0 && (
        <div className="space-y-2">
          {alerts.data.map((a) => (
            <div key={a.alert_id} className="bg-white border border-[#DDE4E8] rounded-[10px] p-3 flex items-start gap-3">
              <span className={`text-[10px] px-2 py-0.5 rounded-full border shrink-0 ${severityColors[a.severity]}`}>
                {a.severity}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-medium text-ink">{typeLabels[a.alert_type] ?? a.alert_type}</span>
                  {a.product && <span className="text-[10px] text-muted">{a.product.sku}</span>}
                  {a.warehouse && <span className="text-[10px] text-muted">· {a.warehouse.code}</span>}
                </div>
                <p className="text-xs text-muted">{a.message}</p>
                <p className="text-[10px] text-muted mt-1">{new Date(a.created_at).toLocaleString('es-PE')}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
