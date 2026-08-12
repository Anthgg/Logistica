import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { purchaseOrderDispatchApi } from '../api/purchaseOrderDispatchApi'
import type {
  DispatchChannel,
  PurchaseOrderCapabilities,
  PurchaseOrderDispatch,
} from '../types/purchase-orders-v2'
import { dispatchChannelLabel, dispatchStatusLabel, generateIdempotencyKey } from '../format'
import { EmptyState, ErrorState, StatusPill } from './ui'
import { Modal } from './ui'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

const CHANNELS: DispatchChannel[] = ['EMAIL', 'PORTAL', 'EDI', 'MANUAL']

export function PurchaseOrderDispatchPanel({
  purchaseOrderId,
  dispatches,
  capabilities,
  onChanged,
}: {
  purchaseOrderId: string
  dispatches: PurchaseOrderDispatch[]
  capabilities: PurchaseOrderCapabilities
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [manualOpen, setManualOpen] = useState<PurchaseOrderDispatch | null>(null)
  const [channel, setChannel] = useState<DispatchChannel>('EMAIL')
  const [contact, setContact] = useState('')
  const [message, setMessage] = useState('')
  const [includeInternal, setIncludeInternal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendGuard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.purchaseOrdersV2.send,
  })

  const handleCreate = async () => {
    if (!contact.trim()) { setError('Contacto obligatorio.'); return }
    setSubmitting(true)
    setError(null)
    try {
      await purchaseOrderDispatchApi.create(purchaseOrderId, { channel, contact_reference: contact.trim(), message: message || null, include_internal_files: includeInternal })
      setOpen(false); setContact(''); setMessage('')
      onChanged()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el envío.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleSend = async (d: PurchaseOrderDispatch) => {
    try {
      const executed = await sendGuard.run(async () => { await purchaseOrderDispatchApi.send(purchaseOrderId, d.id, generateIdempotencyKey()) })
      if (executed) onChanged()
    } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo enviar.') }
  }

  const handleRetry = async (d: PurchaseOrderDispatch) => {
    try { await purchaseOrderDispatchApi.retry(purchaseOrderId, d.id); onChanged() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo reintentar.') }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">No se marca SENT localmente. El envío lo autoriza el backend.</p>
        {capabilities.can_create_dispatch && (
          <button type="button" onClick={() => setOpen(true)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Preparar envío</button>
        )}
      </div>

      {dispatches.length === 0 ? (
        <EmptyState title="Sin envíos" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Canal</th>
                <th className="px-3 py-2.5 text-left">Contacto</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-left">Solicitado</th>
                <th className="px-3 py-2.5 text-left">Enviado</th>
                <th className="px-3 py-2.5 text-left">Entregado</th>
                <th className="px-3 py-2.5 text-left">Error</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {dispatches.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2">{dispatchChannelLabel(d.channel)}</td>
                  <td className="px-3 py-2 font-mono">{d.contact_masked}</td>
                  <td className="px-3 py-2"><StatusPill tone={d.status === 'DELIVERED' ? 'success' : d.status === 'FAILED' ? 'danger' : d.status === 'SENT' ? 'info' : 'warning'}>{dispatchStatusLabel(d.status)}</StatusPill></td>
                  <td className="px-3 py-2">{d.requested_at ?? '—'}</td>
                  <td className="px-3 py-2">{d.sent_at ?? '—'}</td>
                  <td className="px-3 py-2">{d.delivered_at ?? '—'}</td>
                  <td className="px-3 py-2">{d.error_message ?? '—'}</td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex justify-end gap-1">
                      {capabilities.can_send && d.status === 'NOT_SENT' && (
                        <button type="button" disabled={sendGuard.isBlocked} onClick={() => void handleSend(d)} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-50">Enviar</button>
                      )}
                      {capabilities.can_retry_dispatch && d.status === 'FAILED' && (
                        <button type="button" onClick={() => void handleRetry(d)} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-50">Reintentar</button>
                      )}
                      {capabilities.can_mark_manual_delivery && d.status !== 'DELIVERED' && (
                        <button type="button" onClick={() => setManualOpen(d)} className="rounded border border-amber-200 px-2 py-0.5 text-[11px] font-semibold text-amber-700 hover:bg-amber-50">Entrega manual</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={open} onOpenChange={setOpen} title="Preparar envío" footer={
        <>
          <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
          <button type="button" disabled={submitting} onClick={handleCreate} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Creando…' : 'Crear'}</button>
        </>
      }>
        <div className="space-y-3">
          {error && <ErrorState message={error} />}
          <Select value={channel} onValueChange={(v) => setChannel(v as DispatchChannel)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{CHANNELS.map((c) => <SelectItem key={c} value={c}>{dispatchChannelLabel(c)}</SelectItem>)}</SelectContent>
          </Select>
          <div><label className="mb-1 block text-xs font-bold text-slate-700">Contacto</label><input value={contact} onChange={(e) => setContact(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Mensaje" rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
            <input type="checkbox" checked={includeInternal} onChange={(e) => setIncludeInternal(e.target.checked)} className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]" />
            Incluir archivos internos (no recomendado)
          </label>
          <p className="text-[11px] text-slate-500">No se muestran contactos de otra organización. No se guardan contactos nuevos en el maestro automáticamente.</p>
        </div>
      </Modal>

      {manualOpen && (
        <ManualDeliveryDialog purchaseOrderId={purchaseOrderId} dispatch={manualOpen} onClose={() => setManualOpen(null)} onChanged={onChanged} />
      )}
    </div>
  )
}

function ManualDeliveryDialog({
  purchaseOrderId, dispatch, onClose, onChanged,
}: {
  purchaseOrderId: string
  dispatch: PurchaseOrderDispatch
  onClose: () => void
  onChanged: () => void
}) {
  const [deliveredAt, setDeliveredAt] = useState('')
  const [responsible, setResponsible] = useState('')
  const [reference, setReference] = useState('')
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    if (!deliveredAt || !responsible.trim() || !reason.trim()) { setError('Fecha, responsable y motivo obligatorios.'); return }
    setSubmitting(true); setError(null)
    try {
      await purchaseOrderDispatchApi.markManualDelivery(purchaseOrderId, dispatch.id, {
        channel: 'MANUAL', delivered_at: deliveredAt, responsible: responsible.trim(),
        reference: reference || null, reason: reason.trim(),
      })
      onClose(); onChanged()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal open onOpenChange={(o) => !o && onClose()} title="Registrar entrega manual" footer={
      <>
        <button type="button" onClick={onClose} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
        <button type="button" disabled={submitting} onClick={handleSave} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Registrando…' : 'Registrar'}</button>
      </>
    }>
      <div className="space-y-3">
        {error && <ErrorState message={error} />}
        <p className="rounded-lg border border-amber-200 bg-amber-50/50 p-2 text-[11px] text-amber-800">
          Esta acción registra una entrega declarada, no confirma que el proveedor aceptó la orden.
        </p>
        <div><label className="mb-1 block text-xs font-bold text-slate-700">Fecha y hora</label><input type="datetime-local" value={deliveredAt} onChange={(e) => setDeliveredAt(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
        <div><label className="mb-1 block text-xs font-bold text-slate-700">Responsable</label><input value={responsible} onChange={(e) => setResponsible(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
        <div><label className="mb-1 block text-xs font-bold text-slate-700">Referencia</label><input value={reference} onChange={(e) => setReference(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
        <textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Motivo" rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      </div>
    </Modal>
  )
}