import { useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { warehouseGatesApi } from '../api/warehouseGatesApi'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import type { GateType, WarehouseGate, WarehouseGateCreate } from '../types/gate-control'
import { gateStatusLabel, gateTypeLabel } from '../format'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from '../components/ui'
import { Modal } from '../components/ui'

const TYPES: GateType[] = ['INBOUND', 'OUTBOUND', 'BIDIRECTIONAL']

export function WarehouseGatesSettingsPage() {
  const perms = useLogisticsPermissions()
  const canManage = perms.hasPermission(LOGISTICS_PERMISSIONS.gateControl.manageGates)
  const [items, setItems] = useState<WarehouseGate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<WarehouseGateCreate>({ code: '', name: '', warehouse_id: '', type: 'INBOUND', timezone: 'America/Lima' })
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setIsLoading(true); setIsError(false)
    try { const res = await warehouseGatesApi.list({ page: 1, page_size: 100 }); setItems(res.items ?? []) }
    catch (err: unknown) { setIsError(true); setError(err instanceof Error ? err.message : 'No se pudieron cargar los gates.') }
    finally { setIsLoading(false) }
  }

  useEffect(() => { void load() }, [])

  const handleCreate = async () => {
    if (!form.code.trim() || !form.name.trim() || !form.warehouse_id.trim()) { alert('Código, nombre y almacén obligatorios.'); return }
    setSubmitting(true)
    try { await warehouseGatesApi.create(form); setOpen(false); setForm({ code: '', name: '', warehouse_id: '', type: 'INBOUND', timezone: 'America/Lima' }); await load() }
    catch (e) { alert(e instanceof Error ? e.message : 'No se pudo crear.') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">Gates</h1>
        {canManage && <button type="button" onClick={() => setOpen(true)} className="rounded-lg bg-[#1F4E6D] px-3.5 py-2 text-sm font-semibold text-white hover:bg-[#173a55]">Nuevo gate</button>}
      </div>
      {isError ? <ErrorState message={error} onRetry={() => void load()} /> : isLoading ? <TableSkeleton /> : items.length === 0 ? <EmptyState title="Sin gates" /> : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500"><tr>
              <th className="px-3 py-2.5 text-left">Código</th><th className="px-3 py-2.5 text-left">Nombre</th><th className="px-3 py-2.5 text-left">Almacén</th><th className="px-3 py-2.5 text-left">Tipo</th><th className="px-3 py-2.5 text-left">Zona horaria</th><th className="px-3 py-2.5 text-left">Estado</th><th className="px-3 py-2.5 text-right">Acciones</th>
            </tr></thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((g) => (
                <tr key={g.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2 font-mono">{g.code}</td>
                  <td className="px-3 py-2">{g.name}</td>
                  <td className="px-3 py-2">{g.warehouse_name}</td>
                  <td className="px-3 py-2">{gateTypeLabel(g.type)}</td>
                  <td className="px-3 py-2">{g.timezone}</td>
                  <td className="px-3 py-2"><StatusPill tone={g.status === 'ACTIVE' ? 'success' : 'muted'}>{gateStatusLabel(g.status)}</StatusPill></td>
                  <td className="px-3 py-2 text-right">
                    {canManage && g.status === 'ACTIVE' && <button type="button" onClick={async () => { try { await warehouseGatesApi.deactivate(g.id); await load() } catch (e) { alert(e instanceof Error ? e.message : '') } }} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-50">Desactivar</button>}
                    {canManage && g.status === 'INACTIVE' && <button type="button" onClick={async () => { try { await warehouseGatesApi.activate(g.id); await load() } catch (e) { alert(e instanceof Error ? e.message : '') } }} className="rounded border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50">Activar</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={open} onOpenChange={setOpen} title="Nuevo gate" footer={
        <>
          <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
          <button type="button" disabled={submitting} onClick={handleCreate} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Creando…' : 'Crear'}</button>
        </>
      }>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Código</label><input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" /></div>
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Nombre</label><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
            <div><label className="mb-1 block text-xs font-bold text-slate-700">ID almacén</label><input value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" /></div>
            <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v as GateType })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{TYPES.map((t) => <SelectItem key={t} value={t}>{gateTypeLabel(t)}</SelectItem>)}</SelectContent>
            </Select>
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Zona horaria</label><input value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
          </div>
        </div>
      </Modal>
    </div>
  )
}