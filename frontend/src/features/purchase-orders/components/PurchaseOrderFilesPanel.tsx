import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { purchaseOrderFilesApi } from '../api/purchaseOrderFilesApi'
import type {
  PurchaseOrderCapabilities,
  PurchaseOrderFile,
  PurchaseOrderFileClassification,
  PurchaseOrderFileVisibility,
} from '../types/purchase-orders-v2'
import { fileClassificationLabel, fileVisibilityLabel } from '../format'
import { EmptyState, StatusPill } from './ui'
import { Modal } from './ui'

const CLASSIFICATIONS: PurchaseOrderFileClassification[] = ['PROPOSAL', 'SPECIFICATION', 'TERMS', 'BLUEPRINT', 'CERTIFICATE', 'SCHEDULE', 'WARRANTY', 'SUPPORT']
const VISIBILITIES: PurchaseOrderFileVisibility[] = ['INTERNAL_ONLY', 'VISIBLE_TO_SUPPLIER', 'VISIBLE_TO_RECEPTION', 'AUDIT_ONLY']

export function PurchaseOrderFilesPanel({
  purchaseOrderId,
  files,
  capabilities,
  onChanged,
}: {
  purchaseOrderId: string
  files: PurchaseOrderFile[]
  capabilities: PurchaseOrderCapabilities
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [fileId, setFileId] = useState('')
  const [classification, setClassification] = useState<PurchaseOrderFileClassification>('SUPPORT')
  const [visibility, setVisibility] = useState<PurchaseOrderFileVisibility>('INTERNAL_ONLY')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const readOnly = !capabilities.can_manage_files

  const handleAttach = async () => {
    if (!fileId.trim()) { setError('ID de archivo obligatorio.'); return }
    setSubmitting(true)
    setError(null)
    try {
      await purchaseOrderFilesApi.attach(purchaseOrderId, { file_id: fileId.trim(), classification, visibility })
      setOpen(false); setFileId('')
      onChanged()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo asociar el archivo.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleVisibilityChange = async (f: PurchaseOrderFile, v: PurchaseOrderFileVisibility) => {
    if (v === 'VISIBLE_TO_SUPPLIER' && !confirm('¿Hacer visible para el proveedor? Verifica que no contenga datos restringidos.')) return
    try {
      await purchaseOrderFilesApi.updateVisibility(purchaseOrderId, f.id, v)
      onChanged()
    } catch (e) {
      alert(e instanceof Error ? e.message : 'No se pudo cambiar visibilidad.')
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">No se usan archivos en base64. No se guardan signed URLs en el cliente.</p>
        {!readOnly && (
          <button type="button" onClick={() => setOpen(true)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Asociar anexo</button>
        )}
      </div>

      {files.length === 0 ? (
        <EmptyState title="Sin anexos" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Archivo</th>
                <th className="px-3 py-2.5 text-left">Versión</th>
                <th className="px-3 py-2.5 text-left">Clasificación</th>
                <th className="px-3 py-2.5 text-left">Visibilidad</th>
                <th className="px-3 py-2.5 text-left">Hash parcial</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {files.map((f) => (
                <tr key={f.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2">{f.file.name}</td>
                  <td className="px-3 py-2 font-mono">{f.version}</td>
                  <td className="px-3 py-2">{fileClassificationLabel(f.classification)}</td>
                  <td className="px-3 py-2">
                    {!readOnly ? (
                      <Select value={f.visibility} onValueChange={(v) => void handleVisibilityChange(f, v as PurchaseOrderFileVisibility)}>
                        <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
                        <SelectContent>{VISIBILITIES.map((v) => <SelectItem key={v} value={v}>{fileVisibilityLabel(v)}</SelectItem>)}</SelectContent>
                      </Select>
                    ) : fileVisibilityLabel(f.visibility)}
                  </td>
                  <td className="px-3 py-2 font-mono text-[11px] text-slate-500">{f.file.partial_hash?.slice(0, 12) ?? '—'}</td>
                  <td className="px-3 py-2"><StatusPill tone={f.status === 'ACCEPTED' ? 'success' : f.status === 'QUARANTINE' ? 'danger' : 'warning'}>{f.status}</StatusPill></td>
                  <td className="px-3 py-2 text-right">
                    {!readOnly && (
                      <button type="button" onClick={async () => { try { await purchaseOrderFilesApi.detach(purchaseOrderId, f.id); onChanged() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo desasociar.') } }} className="rounded border border-rose-200 px-2 py-0.5 text-[11px] font-semibold text-rose-700 hover:bg-rose-50">Desasociar</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Asociar anexo"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleAttach} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Asociando…' : 'Asociar'}</button>
          </>
        }
      >
        <div className="space-y-3">
          {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>}
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">ID de archivo</label>
            <input value={fileId} onChange={(e) => setFileId(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Clasificación</label>
              <Select value={classification} onValueChange={(v) => setClassification(v as PurchaseOrderFileClassification)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{CLASSIFICATIONS.map((c) => <SelectItem key={c} value={c}>{fileClassificationLabel(c)}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Visibilidad</label>
              <Select value={visibility} onValueChange={(v) => setVisibility(v as PurchaseOrderFileVisibility)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{VISIBILITIES.map((v) => <SelectItem key={v} value={v}>{fileVisibilityLabel(v)}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}