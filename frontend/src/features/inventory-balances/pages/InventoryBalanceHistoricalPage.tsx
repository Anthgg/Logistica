import { useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { Button } from '../../../components/common/Button'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { inventoryBalancesApi } from '../api/inventory-balances-api'
import { DecimalDisplay } from '../components/DecimalDisplay'
import type { InventoryBalanceAsOfRequest, InventoryBalanceAsOfResponse } from '../types/inventory-balances'

export function InventoryBalanceHistoricalPage() {
  const { currentContext } = useLogisticsAccess()
  const organizationId = currentContext?.organization_id

  const [request, setRequest] = useState<InventoryBalanceAsOfRequest>({
    group_by: 'PRODUCT',
  })
  const [result, setResult] = useState<InventoryBalanceAsOfResponse | null>(null)

  const queryHistorical = useMutation(
    async (input: InventoryBalanceAsOfRequest) => inventoryBalancesApi.getBalanceAsOf(input),
    { onSuccess: (data) => setResult(data) },
  )

  const handleQuery = async () => {
    if (!organizationId) return
    await queryHistorical.mutate({ ...request })
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Histórico as-of"
        description="Consulta de saldos en un punto específico del tiempo."
      />

      <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-4 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-muted block mb-1">Fecha/hora de corte</label>
            <input
              type="datetime-local"
              value={request.as_of_date ?? ''}
              onChange={(e) => setRequest((r) => ({ ...r, as_of_date: e.target.value || undefined }))}
              className="w-full text-sm border border-[#DDE4E8] rounded-lg px-3 py-1.5"
            />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Secuencia MOV</label>
            <input
              type="number"
              value={request.as_of_sequence ?? ''}
              onChange={(e) => setRequest((r) => ({ ...r, as_of_sequence: e.target.value ? Number(e.target.value) : undefined }))}
              className="w-full text-sm border border-[#DDE4E8] rounded-lg px-3 py-1.5"
              placeholder="Opcional"
            />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Agrupar por</label>
            <select
              value={request.group_by ?? 'PRODUCT'}
              onChange={(e) => setRequest((r) => ({ ...r, group_by: e.target.value as InventoryBalanceAsOfRequest['group_by'] }))}
              className="w-full text-sm border border-[#DDE4E8] rounded-lg px-3 py-1.5"
            >
              <option value="PRODUCT">Producto</option>
              <option value="WAREHOUSE">Almacén</option>
              <option value="LOCATION">Ubicación</option>
              <option value="POSITION">Posición</option>
            </select>
          </div>
        </div>
        <Button onClick={handleQuery} disabled={queryHistorical.isPending}>
          {queryHistorical.isPending ? 'Consultando...' : 'Consultar histórico'}
        </Button>
      </div>

      {queryHistorical.error && (
        <Alert variant="error">Error al consultar histórico.</Alert>
      )}

      {result && (
        <div className="space-y-3">
          <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-4 text-xs">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <div>Método: <span className="font-medium text-ink">{result.method}</span></div>
              <div>Fecha de corte: <span className="text-ink">{result.as_of_date ? new Date(result.as_of_date).toLocaleString('es-PE') : '—'}</span></div>
              <div>Secuencia: <span className="text-ink">{result.as_of_sequence?.toLocaleString('es-PE') ?? '—'}</span></div>
              <div>Secuencia actual: <span className="text-ink">{result.current_sequence?.toLocaleString('es-PE') ?? '—'}</span></div>
            </div>
            <div className="mt-2">
              Calidad: <span className="text-ink">{result.data_quality}</span>
            </div>
            {result.formulas_used.length > 0 && (
              <p className="mt-1 text-muted">Fórmulas: {result.formulas_used.join(', ')}</p>
            )}
          </div>

          {result.positions.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#DDE4E8]">
                    <th className="text-left py-2 px-2 font-semibold text-muted">Producto</th>
                    <th className="text-left py-2 px-2 font-semibold text-muted">Posición</th>
                    <th className="text-right py-2 px-2 font-semibold text-muted">Físico</th>
                    <th className="text-right py-2 px-2 font-semibold text-muted">Disponible</th>
                    <th className="text-right py-2 px-2 font-semibold text-muted">Reservado</th>
                  </tr>
                </thead>
                <tbody>
                  {result.positions.map((pos) => (
                    <tr key={pos.position_id} className="border-b border-[#EEF1F4]">
                      <td className="py-2 px-2 text-ink">{pos.product.name}</td>
                      <td className="py-2 px-2 text-muted font-mono">{pos.position_id_display}</td>
                      <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={pos.physical} /></td>
                      <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={pos.available} /></td>
                      <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={pos.reserved} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
