import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceCasesApi } from '../api/receptionDifferenceCasesApi'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { EligibleReceiptForDifference } from '../types/reception-differences'

export function CreateReceptionDifferenceCasePage() {
  const navigate = useNavigate()
  const auth = useLogisticsPermissions()
  const [selectedReceiptId, setSelectedReceiptId] = useState<string | null>(null)

  const eligibleQuery = useQuery<EligibleReceiptForDifference[]>(
    ['eligible-receipts'],
    '/logistics/reception-difference-cases/eligible-receipts',
  )

  const createMutation = useMutation(
    async (receiptId: string) => {
      return receptionDifferenceCasesApi.create({ receipt_id: receiptId })
    },
    {
      onSuccess: (result) => {
        if (result && 'case_id' in result) {
          navigate(`/logistics/inbound/reception-differences/${(result as { case_id: string }).case_id}`)
        }
      },
    },
  )

  if (!auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.create)) {
    return (
      <div className="page">
        <div className="panel p-6 text-center text-sm text-slate-500">
          No tienes permisos para crear casos de diferencia.
        </div>
      </div>
    )
  }

  const eligible = eligibleQuery.data ?? []

  return (
    <div className="page">
      <div className="mb-4">
        <h1 className="text-lg font-bold text-slate-800">Crear Caso de Diferencia</h1>
        <p className="text-xs text-slate-500">
          Selecciona una recepción elegible para crear un nuevo caso.
        </p>
      </div>

      {eligibleQuery.isLoading ? (
        <div className="panel p-8 text-center text-sm text-slate-400">Cargando recepciones…</div>
      ) : eligible.length === 0 ? (
        <div className="panel p-8 text-center text-sm text-slate-400">
          No hay recepciones elegibles disponibles.
        </div>
      ) : (
        <div className="space-y-3">
          {eligible.map((r) => (
            <div
              key={r.receipt_id}
              className={`panel cursor-pointer p-4 transition-colors hover:border-[#1F4E6D] ${
                selectedReceiptId === r.receipt_id ? 'border-2 border-[#1F4E6D]' : ''
              }`}
              onClick={() => setSelectedReceiptId(r.receipt_id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') setSelectedReceiptId(r.receipt_id) }}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-mono text-sm font-bold text-slate-800">{r.code}</p>
                  <p className="text-xs text-slate-500">
                    {r.cpv_code && `CPV: ${r.cpv_code}`}
                    {r.cit_code && ` · CIT: ${r.cit_code}`}
                  </p>
                  <p className="text-xs text-slate-500">{r.supplier_name} · {r.warehouse_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">{r.open_candidates} candidato{r.open_candidates !== 1 ? 's' : ''}</p>
                  <p className="text-xs text-slate-500">{r.evidence_count} evidencia{r.evidence_count !== 1 ? 's' : ''}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedReceiptId && (
        <div className="flex justify-end pt-4">
          <button
            type="button"
            onClick={() => createMutation.mutate(selectedReceiptId)}
            disabled={createMutation.isPending}
            className="rounded-lg bg-[#1F4E6D] px-4 py-2 text-sm font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creando…' : 'Crear caso'}
          </button>
        </div>
      )}

      {createMutation.error && (
        <p className="mt-2 text-xs text-rose-600" role="alert">{createMutation.error}</p>
      )}
    </div>
  )
}
