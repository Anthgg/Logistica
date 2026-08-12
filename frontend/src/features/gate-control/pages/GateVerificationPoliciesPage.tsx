import { useEffect, useState } from 'react'
import { gateVerificationPoliciesApi } from '../api/gateVerificationPoliciesApi'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import type { GateVerificationPolicy } from '../types/gate-control'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from '../components/ui'
import { Modal } from '../components/ui'

export function GateVerificationPoliciesPage() {
  const perms = useLogisticsPermissions()
  const canManage = perms.hasPermission(LOGISTICS_PERMISSIONS.gateControl.managePolicies)
  const [items, setItems] = useState<GateVerificationPolicy[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setIsLoading(true); setIsError(false)
    try { setItems(await gateVerificationPoliciesApi.list()) }
    catch (err: unknown) { setIsError(true); setError(err instanceof Error ? err.message : 'No se pudieron cargar las políticas.') }
    finally { setIsLoading(false) }
  }

  useEffect(() => { void load() }, [])

  const handleCreate = async () => {
    if (!code.trim() || !name.trim()) { alert('Código y nombre obligatorios.'); return }
    setSubmitting(true)
    try { await gateVerificationPoliciesApi.create({ code: code.trim(), name: name.trim() }); setOpen(false); setCode(''); setName(''); await load() }
    catch (e) { alert(e instanceof Error ? e.message : 'No se pudo crear.') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">Políticas de verificación</h1>
        {canManage && <button type="button" onClick={() => setOpen(true)} className="rounded-lg bg-[#1F4E6D] px-3.5 py-2 text-sm font-semibold text-white hover:bg-[#173a55]">Nueva política</button>}
      </div>
      <p className="text-xs text-slate-500">No se permiten scripts o fórmulas libres. No se edita una versión activa.</p>
      {isError ? <ErrorState message={error} onRetry={() => void load()} /> : isLoading ? <TableSkeleton /> : items.length === 0 ? <EmptyState title="Sin políticas" /> : (
        <div className="space-y-2">
          {items.map((p) => (
            <div key={p.id} className="rounded-xl border border-slate-200 p-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold">{p.code} — {p.name}</span>
                <StatusPill tone={p.status === 'ACTIVE' ? 'success' : 'muted'}>{p.status}</StatusPill>
              </div>
              <div className="mt-1 text-slate-500">Versión activa: {p.active_version?.version ?? '—'} · Checks: {p.active_version?.checks.length ?? 0}</div>
            </div>
          ))}
        </div>
      )}
      <Modal open={open} onOpenChange={setOpen} title="Nueva política" footer={
        <>
          <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
          <button type="button" disabled={submitting} onClick={handleCreate} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Creando…' : 'Crear'}</button>
        </>
      }>
        <div className="space-y-3">
          <div><label className="mb-1 block text-xs font-bold text-slate-700">Código</label><input value={code} onChange={(e) => setCode(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" /></div>
          <div><label className="mb-1 block text-xs font-bold text-slate-700">Nombre</label><input value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
        </div>
      </Modal>
    </div>
  )
}