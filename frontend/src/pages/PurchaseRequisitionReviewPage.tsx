import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { purchaseRequisitionsApi } from '../api/purchase-requisitions-api'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import {
  RequisitionPriorityBadge,
  RequisitionStatusBadge,
} from '../components/purchase-requisitions/RequisitionStatusBadge'
import type { PurchaseRequisitionSummary } from '../types/purchase-requisitions'

export function PurchaseRequisitionReviewPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<PurchaseRequisitionSummary[]>([])
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await purchaseRequisitionsApi.list({ pending_my_review: true })
      setItems(res.items || [])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6 text-xs">
      <PageHeader
        title="Bandeja de Revisión y Aprobación de REQ"
        description="Requerimientos de compra pendientes de evaluación y dictamen autorizado."
      />

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500 font-medium">
          No tienes requerimientos de compra pendientes de revisión en este momento.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Código REQ</th>
                <th className="px-4 py-3 text-left font-semibold">Solicitante</th>
                <th className="px-4 py-3 text-left font-semibold">Centro de Costo</th>
                <th className="px-4 py-3 text-center font-semibold">Prioridad</th>
                <th className="px-4 py-3 text-left font-semibold">Fecha Requerida</th>
                <th className="px-4 py-3 text-center font-semibold">Estado</th>
                <th className="px-4 py-3 text-right font-semibold">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {items.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => navigate(`/logistics/purchasing/requisitions/${row.id}`)}
                  className="cursor-pointer hover:bg-slate-50 transition-colors"
                >
                  <td className="px-4 py-3 font-mono font-bold text-indigo-700 text-sm">
                    {row.requisition_code}
                  </td>
                  <td className="px-4 py-3 font-bold text-slate-800">{row.applicant_user_name}</td>
                  <td className="px-4 py-3 text-slate-700 font-medium">{row.cost_center_name}</td>
                  <td className="px-4 py-3 text-center">
                    <RequisitionPriorityBadge priority={row.priority} size="sm" />
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-700">
                    {new Date(row.required_date).toLocaleDateString('es-PE')}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <RequisitionStatusBadge status={row.status} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/logistics/purchasing/requisitions/${row.id}`)
                      }}
                      className="font-semibold text-indigo-600 hover:underline"
                    >
                      Evaluar Solicitud →
                    </button>
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
