import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { purchaseOrderAcknowledgementsApi } from '../api/purchaseOrderAcknowledgementsApi'
import type {
  AcknowledgementType,
  DispatchChannel,
  PurchaseOrderAcknowledgement,
  PurchaseOrderCapabilities,
} from '../types/purchase-orders-v2'
import { acknowledgementStatusLabel, acknowledgementTypeLabel, dispatchChannelLabel } from '../format'
import { EmptyState, StatusPill } from './ui'
import { Modal } from './ui'

const ACK_TYPES: AcknowledgementType[] = ['EMAIL_REPLY', 'PORTAL_CONFIRM', 'SIGNED_DOCUMENT', 'MANUAL']
const CHANNELS: DispatchChannel[] = ['EMAIL', 'PORTAL', 'EDI', 'MANUAL']

export function PurchaseOrderAcknowledgementsPanel({
  purchaseOrderId,
  acknowledgements,
  capabilities,
  onChanged,
}: {
  purchaseOrderId: string
  acknowledgements: PurchaseOrderAcknowledgement[]
  capabilities: PurchaseOrderCapabilities
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [type, setType] = useState<AcknowledgementType>('MANUAL')
  const [reference, setReference] = useState('')
  const [receivedAt, setReceivedAt] = useState('')
  const [channel, setChannel] = useState<DispatchChannel>('EMAIL')
  const [name, setName] = useState('')
  const [comment, setComment] = useState('')
  const [fileId, setFileId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    setSubmitting(true); setError(null)
    try {
      await purchaseOrderAcknowledgementsApi.create(purchaseOrderId, {
        type, reference: reference || null, received_at: receivedAt || null,
        channel, name: name || null, comment: comment || null, file_id: fileId || null,
      })
      setOpen(false); setReference(''); setReceivedAt(''); setName(''); setComment(''); setFileId('')
      onChanged()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar el acuse.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">No se modifica la OC desde el acuse.</p>
        {capabilities.can_create_acknowledgement && (
          <button type="button" onClick={() => setOpen(true)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Registrar acuse</button>
        )}
      </div>

      {acknowledgements.length === 0 ? (
        <EmptyState title="Sin acuses" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Tipo</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-left">Referencia</th>
                <th className="px-3 py-2.5 text-left">Fecha</th>
                <th className="px-3 py-2.5 text-left">Canal</th>
                <th className="px-3 py-2.5 text-left">Nombre</th>
                <th className="px-3 py-2.5 text-left">Comentario</th>
                <th className="px-3 py-2.5 text-center">Validado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {acknowledgements.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2">{acknowledgementTypeLabel(a.type)}</td>
                  <td className="px-3 py-2"><StatusPill tone={a.status === 'VALIDATED' ? 'success' : a.status === 'REJECTED' ? 'danger' : a.status === 'RECEIVED' ? 'info' : 'warning'}>{acknowledgementStatusLabel(a.status)}</StatusPill></td>
                  <td className="px-3 py-2 font-mono">{a.reference ?? '—'}</td>
                  <td className="px-3 py-2">{a.received_at ?? '—'}</td>
                  <td className="px-3 py-2">{a.channel ? dispatchChannelLabel(a.channel) : '—'}</td>
                  <td className="px-3 py-2">{a.name ?? '—'}</td>
                  <td className="px-3 py-2">{a.comment ?? '—'}</td>
                  <td className="px-3 py-2 text-center">{a.validated ? 'Sí' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={open} onOpenChange={setOpen} title="Registrar acuse" footer={
        <>
          <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
          <button type="button" disabled={submitting} onClick={handleCreate} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Registrando…' : 'Registrar'}</button>
        </>
      }>
        <div className="space-y-3">
          {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>}
          <Select value={type} onValueChange={(v) => setType(v as AcknowledgementType)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{ACK_TYPES.map((t) => <SelectItem key={t} value={t}>{acknowledgementTypeLabel(t)}</SelectItem>)}</SelectContent>
          </Select>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Referencia</label><input value={reference} onChange={(e) => setReference(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Fecha</label><input type="datetime-local" value={receivedAt} onChange={(e) => setReceivedAt(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
            <Select value={channel} onValueChange={(v) => setChannel(v as DispatchChannel)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{CHANNELS.map((c) => <SelectItem key={c} value={c}>{dispatchChannelLabel(c)}</SelectItem>)}</SelectContent>
            </Select>
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Nombre</label><input value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
          </div>
          <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Comentario" rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <div><label className="mb-1 block text-xs font-bold text-slate-700">ID archivo (opcional)</label><input value={fileId} onChange={(e) => setFileId(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" /></div>
        </div>
      </Modal>
    </div>
  )
}