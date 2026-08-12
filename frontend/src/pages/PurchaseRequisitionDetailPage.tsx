import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { purchaseRequisitionsApi } from '../api/purchase-requisitions-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import {
  ApprovePurchaseRequisitionDialog,
  RejectPurchaseRequisitionDialog,
  ReturnPurchaseRequisitionDialog,
  SubmitPurchaseRequisitionDialog,
} from '../components/purchase-requisitions/SubmitPurchaseRequisitionDialog'
import { PurchaseRequisitionCommentsPanel, PurchaseRequisitionDocumentPanel } from '../components/purchase-requisitions/PurchaseRequisitionCommentsPanel'
import { PurchaseRequisitionHistoryTimeline } from '../components/purchase-requisitions/PurchaseRequisitionHistoryTimeline'
import { PurchaseRequisitionRevisionsPanel } from '../components/purchase-requisitions/PurchaseRequisitionRevisionsPanel'
import {
  RequisitionPriorityBadge,
  RequisitionStatusBadge,
} from '../components/purchase-requisitions/RequisitionStatusBadge'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import type {
  PurchaseRequisition,
  PurchaseRequisitionComment,
  PurchaseRequisitionDecision,
  PurchaseRequisitionRevision,
} from '../types/purchase-requisitions'

type ReqTab = 'summary' | 'lines' | 'comments' | 'decisions' | 'revisions' | 'document' | 'history'

export function PurchaseRequisitionDetailPage() {
  const { requisitionId } = useParams<{ requisitionId: string }>()
  const navigate = useNavigate()
  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [requisition, setRequisition] = useState<PurchaseRequisition | null>(null)
  const [revisions, setRevisions] = useState<PurchaseRequisitionRevision[]>([])
  const [comments, setComments] = useState<PurchaseRequisitionComment[]>([])
  const [decisions, setDecisions] = useState<PurchaseRequisitionDecision[]>([])
  const [history, setHistory] = useState<Array<{ id: string; action: string; description: string; user_name: string; created_at: string }>>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setTab] = useState<ReqTab>('summary')

  // Modals
  const [showSubmitModal, setShowSubmitModal] = useState(false)
  const [showApproveModal, setShowApproveModal] = useState(false)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [showReturnModal, setShowReturnModal] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)

  const loadAll = useCallback(async () => {
    if (!requisitionId) return
    setLoading(true)
    try {
      const [req, revs, comms, decs, hist] = await Promise.all([
        purchaseRequisitionsApi.get(requisitionId),
        purchaseRequisitionsApi.listRevisions(requisitionId).catch(() => []),
        purchaseRequisitionsApi.listComments(requisitionId).catch(() => []),
        purchaseRequisitionsApi.listDecisions(requisitionId).catch(() => []),
        purchaseRequisitionsApi.getHistory(requisitionId).catch(() => []),
      ])
      setRequisition(req)
      setRevisions(revs)
      setComments(comms)
      setDecisions(decs)
      setHistory(hist)
    } finally {
      setLoading(false)
    }
  }, [requisitionId])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  if (loading) return <LoadingSkeleton rows={10} />
  if (!requisition) {
    return (
      <div className="mx-auto max-w-5xl p-6 text-center space-y-4">
        <p className="text-slate-500">No se encontró el requerimiento de compra especificado.</p>
        <Button onClick={() => navigate('/logistics/purchasing/requisitions')}>Volver al catálogo</Button>
      </div>
    )
  }

  const { capabilities } = requisition

  // Action Handlers
  const handleSubmitReq = async () => {
    setActionLoading(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await purchaseRequisitionsApi.submit(requisition.id)
      })
      if (executed) {
        setShowSubmitModal(false)
        void loadAll()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al enviar requerimiento')
    } finally {
      setActionLoading(false)
    }
  }

  const handleApproveReq = async (comm: string, cond?: string) => {
    setActionLoading(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await purchaseRequisitionsApi.approve(requisition.id, comm, cond)
      })
      if (executed) {
        setShowApproveModal(false)
        void loadAll()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al aprobar requerimiento')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRejectReq = async (comm: string) => {
    setActionLoading(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await purchaseRequisitionsApi.reject(requisition.id, comm)
      })
      if (executed) {
        setShowRejectModal(false)
        void loadAll()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al rechazar requerimiento')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReturnReq = async (comm: string) => {
    setActionLoading(true)
    try {
      await purchaseRequisitionsApi.returnForChanges(requisition.id, comm)
      setShowReturnModal(false)
      void loadAll()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al devolver requerimiento')
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6 text-xs">
      {/* Header */}
      <PageHeader
        eyebrow={`Código: ${requisition.requisition_code} · Revisión: v${requisition.active_revision_number}`}
        title={`Requerimiento ${requisition.requisition_code}`}
        description={`Centro de Costo: ${requisition.cost_center_name} · Solicitado por ${requisition.applicant_user_name}`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <RequisitionStatusBadge status={requisition.status} />
            <RequisitionPriorityBadge priority={requisition.priority} />

            {/* Workflow Buttons */}
            {capabilities?.can_update && (
              <Button variant="secondary" onClick={() => navigate(`/logistics/purchasing/requisitions/${requisition.id}/edit`)}>
                Editar Borrador
              </Button>
            )}

            {capabilities?.can_submit && (
              <Button onClick={() => setShowSubmitModal(true)}>
                Enviar Requerimiento (Step-Up)
              </Button>
            )}

            {capabilities?.can_approve && (
              <Button onClick={() => setShowApproveModal(true)}>
                Aprobar (Step-Up)
              </Button>
            )}

            {capabilities?.can_return && (
              <Button variant="secondary" onClick={() => setShowReturnModal(true)}>
                Devolver para Cambios
              </Button>
            )}

            {capabilities?.can_reject && (
              <Button variant="secondary" onClick={() => setShowRejectModal(true)}>
                Rechazar (Step-Up)
              </Button>
            )}
          </div>
        }
      />

      {/* Tabs Bar */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-1" aria-label="Pestañas de Requerimiento">
          {[
            { id: 'summary', label: 'Resumen General' },
            { id: 'lines', label: `Líneas (${requisition.lines.length})` },
            { id: 'comments', label: `Comentarios (${comments.length})` },
            { id: 'decisions', label: `Decisiones (${decisions.length})` },
            { id: 'revisions', label: `Revisiones (${revisions.length})` },
            { id: 'document', label: 'Documento REQ' },
            { id: 'history', label: 'Historial' },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id as ReqTab)}
              className={`px-4 py-2.5 font-semibold border-b-2 transition-colors ${
                activeTab === t.id
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Contents */}
      <div className="pt-2">
        {activeTab === 'summary' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:grid-cols-4">
              <div>
                <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Centro de Costo</span>
                <span className="font-bold text-slate-800 text-sm">{requisition.cost_center_name}</span>
              </div>
              <div>
                <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Fecha Requerida</span>
                <span className="font-mono font-bold text-slate-800 text-sm">
                  {new Date(requisition.required_date).toLocaleDateString('es-PE')}
                </span>
              </div>
              <div>
                <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Almacén Destino</span>
                <span className="font-bold text-indigo-700 text-sm">{requisition.destination_warehouse_name}</span>
              </div>
              <div>
                <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Solicitante</span>
                <span className="font-bold text-slate-800 text-sm">{requisition.applicant_user_name}</span>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-3">
              <h4 className="font-bold text-slate-800 text-sm">Justificación Operacional</h4>
              <p className="text-slate-700 leading-relaxed">{requisition.summary_justification}</p>
              {requisition.business_purpose && (
                <div className="pt-2 border-t border-slate-100">
                  <span className="font-bold text-slate-500 text-[11px] block">Propósito Empresarial:</span>
                  <p className="text-slate-600">{requisition.business_purpose}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'lines' && (
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">N.º</th>
                  <th className="px-4 py-3 text-left font-semibold">SKU</th>
                  <th className="px-4 py-3 text-left font-semibold">Producto</th>
                  <th className="px-4 py-3 text-right font-semibold">Cantidad</th>
                  <th className="px-4 py-3 text-left font-semibold">Unidad</th>
                  <th className="px-4 py-3 text-right font-semibold">Cant. Base Autorizada</th>
                  <th className="px-4 py-3 text-left font-semibold">Fecha Requerida</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {requisition.lines.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono font-bold text-slate-500">{l.line_number}</td>
                    <td className="px-4 py-3 font-mono font-bold text-indigo-700">{l.product_sku}</td>
                    <td className="px-4 py-3 font-bold text-slate-800">{l.product_name}</td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-slate-900">{l.requested_quantity}</td>
                    <td className="px-4 py-3 text-slate-600">{l.unit_of_measure_code}</td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-indigo-900">
                      {l.base_quantity ? `${l.base_quantity} ${l.base_unit_code}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-slate-600 font-mono">
                      {new Date(l.required_date).toLocaleDateString('es-PE')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'comments' && (
          <PurchaseRequisitionCommentsPanel
            requisitionId={requisition.id}
            comments={comments}
            onCommentAdded={loadAll}
            canComment={capabilities?.can_comment}
          />
        )}

        {activeTab === 'revisions' && (
          <PurchaseRequisitionRevisionsPanel requisitionId={requisition.id} revisions={revisions} />
        )}

        {activeTab === 'document' && (
          <PurchaseRequisitionDocumentPanel
            requisitionCode={requisition.requisition_code}
            activeRevisionNumber={requisition.active_revision_number}
          />
        )}

        {activeTab === 'history' && (
          <PurchaseRequisitionHistoryTimeline history={history} />
        )}
      </div>

      {/* Modals */}
      <SubmitPurchaseRequisitionDialog
        isOpen={showSubmitModal}
        isSubmitting={actionLoading}
        requisition={requisition}
        onSubmit={handleSubmitReq}
        onClose={() => setShowSubmitModal(false)}
      />

      <ApprovePurchaseRequisitionDialog
        isOpen={showApproveModal}
        isSubmitting={actionLoading}
        requisitionCode={requisition.requisition_code}
        onApprove={handleApproveReq}
        onClose={() => setShowApproveModal(false)}
      />

      <RejectPurchaseRequisitionDialog
        isOpen={showRejectModal}
        isSubmitting={actionLoading}
        requisitionCode={requisition.requisition_code}
        onReject={handleRejectReq}
        onClose={() => setShowRejectModal(false)}
      />

      <ReturnPurchaseRequisitionDialog
        isOpen={showReturnModal}
        isSubmitting={actionLoading}
        requisitionCode={requisition.requisition_code}
        onReturn={handleReturnReq}
        onClose={() => setShowReturnModal(false)}
      />
    </div>
  )
}
