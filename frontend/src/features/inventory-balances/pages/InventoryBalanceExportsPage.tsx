import { useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { Button } from '../../../components/common/Button'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { getErrorMessage } from '../../../utils/errors'
import { inventoryBalanceExportsApi } from '../api/inventory-balance-exports-api'
import type { InventoryBalanceExport, InventoryBalanceExportRequest } from '../types/inventory-balances'

export function InventoryBalanceExportsPage() {
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canExport = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.export)
  const organizationId = currentContext?.organization_id

  const [format, setFormat] = useState<InventoryBalanceExportFormat>('CSV')

  const exports = useQuery<{ items: InventoryBalanceExport[] }>(
    ['inventory-balances', 'exports', organizationId ?? ''],
    '/logistics/inventory/balances/exports',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: Boolean(organizationId) },
  )

  const createExport = useMutation(
    async (input: InventoryBalanceExportRequest) => inventoryBalanceExportsApi.createExport(input),
    { onSuccess: () => { void exports.refetch() } },
  )

  const handleExport = async () => {
    if (!organizationId) return
    await createExport.mutate({
      format,
      filters: { organization_id: organizationId },
    })
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Exportaciones de saldo"
        description="Exportación técnica de saldos en diversos formatos."
        actions={
          canExport ? (
            <div className="flex gap-2 items-center">
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value as InventoryBalanceExportFormat)}
                className="text-sm border border-[#DDE4E8] rounded-lg px-3 py-1.5"
              >
                <option value="CSV">CSV</option>
                <option value="XLSX">XLSX</option>
                <option value="PDF">PDF técnico</option>
              </select>
              <Button onClick={handleExport} disabled={createExport.isPending}>
                {createExport.isPending ? 'Exportando...' : 'Exportar'}
              </Button>
            </div>
          ) : undefined
        }
      />

      {exports.isLoading && <LoadingSkeleton rows={6} />}
      {exports.isError && <Alert variant="error">{getErrorMessage(exports.error)}</Alert>}

      {exports.data && exports.data.items.length === 0 && (
        <Alert variant="info">No hay exportaciones registradas.</Alert>
      )}

      {exports.data && exports.data.items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#DDE4E8]">
                <th className="text-left py-2 px-2 font-semibold text-muted">Formato</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Estado</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Corte</th>
                <th className="text-right py-2 px-2 font-semibold text-muted">Secuencia</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Calidad</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Solicitante</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Archivo</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {exports.data.items.map((e) => (
                <tr key={e.export_id} className="border-b border-[#EEF1F4]">
                  <td className="py-2 px-2 text-ink">{e.format}</td>
                  <td className="py-2 px-2">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                      e.status === 'COMPLETED' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' :
                      e.status === 'RUNNING' ? 'border-blue-200 bg-blue-50 text-blue-700' :
                      e.status === 'FAILED' ? 'border-rose-200 bg-rose-50 text-rose-700' :
                      'border-slate-200 bg-slate-50 text-slate-600'
                    }`}>{e.status}</span>
                  </td>
                  <td className="py-2 px-2 text-muted">{new Date(e.balance_as_of).toLocaleString('es-PE')}</td>
                  <td className="py-2 px-2 text-right text-ink">{e.balance_sequence?.toLocaleString('es-PE') ?? '—'}</td>
                  <td className="py-2 px-2 text-muted">{e.data_quality}</td>
                  <td className="py-2 px-2 text-muted">{e.requested_by?.display_name ?? '—'}</td>
                  <td className="py-2 px-2 text-muted">{e.file_name ?? '—'}</td>
                  <td className="py-2 px-2">
                    {e.status === 'COMPLETED' && e.file_url && (
                      <a href={e.file_url} className="text-primary hover:underline text-[10px]" download>
                        Descargar
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

type InventoryBalanceExportFormat = 'CSV' | 'XLSX' | 'PDF'
