import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { purchaseOrderAmendmentsApi } from '../api/purchaseOrderAmendmentsApi'
import type {
  AmendmentType,
  PurchaseOrderAmendment,
  PurchaseOrderCapabilities,
} from '../types/purchase-orders-v2'
import { amendmentStatusLabel, amendmentTypeLabel, generateIdempotencyKey } from '../format'
import { EmptyState, StatusPill } from './ui'
import { Modal } from './ui'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

const TYPES: AmendmentType[] = ['QUANTITY_REDUCTION', 'RESCHEDULE', 'DESTINATION_CHANGE', 'TERMS_CHANGE', 'PRICE_CHANGE_WITH_NEW_DECISION', 'CANCELLATION', 'OTHER']

export function PurchaseOrderAmendmentsPanel({
  purchaseOrderId,
  amendments,
  capabilities,
  onChanged,
}: {
  purchaseOrderId: string
  amendments: PurchaseOrderAmendment[]
  capabilities: PurchaseOrderCapabilities
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [type, setType] = useState<AmendmentType>('RESCHEDULE')
  const [reason, setReason] = useState('')
  const [impact, setImpact] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const issueGuard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.purchaseOrdersV2.issue,
  })

  const handleCreate = async () => {
    if (!reason.trim()) { setError('Motivo obligatorio.'); return }
    setSubmitting(true); setError(null)
    try {
      await purchaseOrderAmendmentsApi.create(purchaseOrderId, { type, reason: reason.trim(), impact_summary: impact || null })
      setOpen(false); setReason(''); setImpact('')
      onChanged()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo crear la enmienda.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleIssue = async (a: PurchaseOrderAmendment) => {
    try {
      const executed = await issueGuard.run(async () => { await purchaseOrderAmendmentsApi.issue(purchaseOrderId, a.id, generateIdempotencyKey()) })
      if (executed) onChanged()
    } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo emitir.') }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">No se edita la OC original. La enmienda es un documento separado.</p>
        {capabilities.can_create_amendment && (
          <button type="button" onClick={() => setOpen(true)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Nueva enmienda</button>
        )}
      </div>

      {amendments.length === 0 ? (
        <EmptyState title="Sin enmiendas" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">N.º</th>
                <th className="px-3 py-2.5 text-left">Tipo</th>
                <th className="px-3 py-2.5 text-left">Motivo</th>
                <th className="px-3 py-2.5 text-left">Impacto</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-left">Aprobación</th>
                <th className="px-3 py-2.5 text-left">Documento</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {amendments.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2 font-mono">{a.amendment_number}</td>
                  <td className="px-3 py-2">{amendmentTypeLabel(a.type)}</td>
                  <td className="px-3 py-2">{a.reason}</td>
                  <td className="px-3 py-2">{a.impact_summary ?? '—'}</td>
                  <td className="px-3 py-2"><StatusPill tone={a.status === 'ISSUED' ? 'success' : a.status === 'CANCELLED' ? 'danger' : 'info'}>{amendmentStatusLabel(a.status)}</StatusPill></td>
                  <td className="px-3 py-2">{a.approval_status ?? '—'}</td>
                  <td className="px-3 py-2 font-mono">{a.document_code ?? '—'}</td>
                  <td className="px-3 py-2 text-right">
                    {capabilities.can_issue && a.status === 'APPROVED' && (
                      <button type="button" disabled={issueGuard.isBlocked} onClick={() => void handleIssue(a)} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-50">Emitir</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={open} onOpenChange={setOpen} title="Nueva enmienda" footer={
        <>
          <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
          <button type="button" disabled={submitting} onClick={handleCreate} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Creando…' : 'Crear'}</button>
        </>
      }>
        <div className="space-y-3">
          {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>}
          <Select value={type} onValueChange={(v) => setType(v as AmendmentType)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{TYPES.map((t) => <SelectItem key={t} value={t}>{amendmentTypeLabel(t)}</SelectItem>)}</SelectContent>
          </Select>
          <textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Motivo" rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <textarea value={impact} onChange={(e) => setImpact(e.target.value)} placeholder="Impacto (opcional)" rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
      </Modal>
    </div>
  )
}