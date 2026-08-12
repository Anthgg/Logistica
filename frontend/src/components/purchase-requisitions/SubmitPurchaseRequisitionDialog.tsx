import { useState } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type { PurchaseRequisition } from '../../types/purchase-requisitions'

interface SubmitProps {
  isOpen: boolean
  isSubmitting: boolean
  requisition: PurchaseRequisition
  onSubmit: () => void
  onClose: () => void
}

export function SubmitPurchaseRequisitionDialog({
  isOpen,
  isSubmitting,
  requisition,
  onSubmit,
  onClose,
}: SubmitProps) {
  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="submit-req-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="submit-req-title" className="text-base font-bold text-slate-800">
          Enviar Requerimiento ({requisition.requisition_code})
        </h3>

        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-amber-900 space-y-1">
          <p className="font-bold flex items-center gap-1.5"><LogisticsIcon name="alert" size={14} aria-hidden /> Congelamiento de Revisión (v{requisition.active_revision_number}):</p>
          <p className="text-[11px] text-amber-800">
            Al enviar, esta revisión quedará inmutable. Las correcciones o cambios posteriores solicitados crearán una nueva revisión conservando el código REQ.
          </p>
        </div>

        <div className="space-y-1 text-slate-700 font-medium">
          <div>Centro de Costo: <strong>{requisition.cost_center_name}</strong></div>
          <div>Líneas totales: <strong>{requisition.lines.length}</strong></div>
          <div>Prioridad: <strong className="text-indigo-700">{requisition.priority}</strong></div>
        </div>

        <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
          <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={onSubmit}
            isLoading={isSubmitting}
            loadingLabel="Enviando..."
          >
            Confirmar Envío (Step-Up)
          </Button>
        </div>
      </div>
    </div>
  )
}

interface ApproveProps {
  isOpen: boolean
  isSubmitting: boolean
  requisitionCode: string
  onApprove: (comments: string, conditions?: string) => void
  onClose: () => void
}

export function ApprovePurchaseRequisitionDialog({
  isOpen,
  isSubmitting,
  requisitionCode,
  onApprove,
  onClose,
}: ApproveProps) {
  const [comments, setComments] = useState('')
  const [conditions, setConditions] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!comments.trim() || isSubmitting) return
    onApprove(comments.trim(), conditions.trim() || undefined)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="approve-req-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="approve-req-title" className="text-base font-bold text-emerald-800">
          Aprobar Requerimiento ({requisitionCode})
        </h3>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Comentario de Aprobación *</label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={2}
              required
              placeholder="Indica el motivo o conformidad de aprobación..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Condiciones de Aprobación (Opcional)</label>
            <input
              type="text"
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              placeholder="Ej. Sujeto a disponibilidad de transporte..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!comments.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Aprobando..."
            >
              Confirmar Aprobación (Step-Up)
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

interface RejectProps {
  isOpen: boolean
  isSubmitting: boolean
  requisitionCode: string
  onReject: (comments: string) => void
  onClose: () => void
}

export function RejectPurchaseRequisitionDialog({
  isOpen,
  isSubmitting,
  requisitionCode,
  onReject,
  onClose,
}: RejectProps) {
  const [comments, setComments] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!comments.trim() || isSubmitting) return
    onReject(comments.trim())
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="reject-req-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="reject-req-title" className="text-base font-bold text-rose-700">
          Rechazar Requerimiento ({requisitionCode})
        </h3>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo Obligatorio de Rechazo *</label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={3}
              required
              placeholder="Indica la justificación del rechazo definitivo..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!comments.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Rechazando..."
            >
              Confirmar Rechazo (Step-Up)
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

interface ReturnProps {
  isOpen: boolean
  isSubmitting: boolean
  requisitionCode: string
  onReturn: (comments: string) => void
  onClose: () => void
}

export function ReturnPurchaseRequisitionDialog({
  isOpen,
  isSubmitting,
  requisitionCode,
  onReturn,
  onClose,
}: ReturnProps) {
  const [comments, setComments] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!comments.trim() || isSubmitting) return
    onReturn(comments.trim())
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="return-req-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="return-req-title" className="text-base font-bold text-amber-800">
          Devolver para Cambios ({requisitionCode})
        </h3>

        <p className="text-slate-600">
          Al devolver, se habilitará una nueva revisión editable conservando el código REQ.
        </p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Observaciones para el Solicitante *</label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={3}
              required
              placeholder="Indica qué líneas o campos deben ser corregidos..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!comments.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Devolviendo..."
            >
              Confirmar Devolución
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
