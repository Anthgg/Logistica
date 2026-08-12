import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { warehouseGatesApi } from '../api/warehouseGatesApi'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { gateCheckInsApi } from '../api/gateCheckInsApi'
import type { GateTodaySummary, GateCheckIn, WarehouseGate, GateCheckInListQuery } from '../types/gate-control'
import { checkInStatusLabel, arrivalClassificationLabel, formatServerTime } from '../format'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from '../components/ui'

type TabKey = 'expected' | 'at_gate' | 'in_verification' | 'held' | 'finished'

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'expected', label: 'Esperadas' },
  { key: 'at_gate', label: 'En puerta' },
  { key: 'in_verification', label: 'En verificación' },
  { key: 'held', label: 'Retenidas' },
  { key: 'finished', label: 'Finalizadas' },
]

export function GateControlDashboardPage() {
  const navigate = useNavigate()
  const [gateId, setGateId] = useState<string>('')
  const [gates, setGates] = useState<WarehouseGate[]>([])
  const [summary, setSummary] = useState<GateTodaySummary | null>(null)
  const [items, setItems] = useState<GateCheckIn[]>([])
  const [tab, setTab] = useState<TabKey>('expected')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 350)
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    warehouseGatesApi.list({ status: 'ACTIVE', page: 1, page_size: 100 }).then((res) => {
      setGates(res.items ?? [])
      if (res.items && res.items.length > 0 && !gateId) setGateId(res.items[0]!.id)
    }).catch(() => setGates([]))
  }, [])

  useEffect(() => {
    if (!gateId) return
    warehouseGatesApi.getTodaySummary(gateId).then(setSummary).catch(() => setSummary(null))
  }, [gateId])

  useEffect(() => {
    if (!gateId) return
    setIsLoading(true)
    setIsError(false)
    const query: GateCheckInListQuery = { gate_id: gateId, search: debouncedSearch || undefined, tab, page: 1, page_size: 50 }
    gateCheckInsApi.list(query).then((res) => { setItems(res.items ?? []) }).catch((err: unknown) => {
      setIsError(true); setErrorMessage(err instanceof Error ? err.message : 'No se pudo cargar la cola.')
    }).finally(() => setIsLoading(false))
  }, [gateId, debouncedSearch, tab])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Control de puerta</h1>
          <p className="text-xs text-slate-500">Sin asignar muelles, iniciar descargas o registrar recepciones.</p>
        </div>
        <button type="button" onClick={() => navigate('/logistics/inbound/gate-control/check-ins/new')} className="rounded-lg bg-[#1F4E6D] px-3.5 py-2 text-sm font-semibold text-white hover:bg-[#173a55]">
          Nuevo check-in
        </button>
      </div>

      {/* Selector de gate */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
        <div className="flex-1">
          <label htmlFor="gate-select" className="mb-1 block text-xs font-bold text-slate-700">Gate</label>
          <Select value={gateId} onValueChange={setGateId}>
            <SelectTrigger id="gate-select"><SelectValue placeholder="Selecciona un gate" /></SelectTrigger>
            <SelectContent>
              {gates.map((g) => <SelectItem key={g.id} value={g.id}>{g.code} — {g.name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        {summary && (
          <div className="text-xs text-slate-500">
            Hora del servidor: <span className="font-mono font-semibold text-slate-800">{formatServerTime(summary.server_time, summary.timezone)}</span>
          </div>
        )}
      </div>

      {/* Resumen de conteos */}
      {summary && (
        <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
          {[
            { label: 'Esperadas hoy', value: summary.expected_today },
            { label: 'Llegadas registradas', value: summary.arrivals_registered },
            { label: 'En verificación', value: summary.verifications_in_progress },
            { label: 'Retenidos', value: summary.held_at_gate },
            { label: 'Esperando supervisor', value: summary.waiting_supervisor },
            { label: 'Autorizados', value: summary.authorized },
            { label: 'Autorizados c/obs.', value: summary.authorized_with_observations },
            { label: 'Denegados', value: summary.denied },
          ].map((s) => (
            <div key={s.label} className="rounded-lg border border-slate-200 bg-white p-2.5">
              <div className="text-slate-500">{s.label}</div>
              <div className="mt-0.5 font-mono text-lg font-bold text-slate-800">{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div role="tablist" aria-label="Estado de la cola" className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/60 p-1">
        {TABS.map((t) => (
          <button key={t.key} role="tab" aria-selected={tab === t.key} type="button" onClick={() => setTab(t.key)}
            className={tab === t.key ? 'rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-[#1F4E6D] shadow-xs' : 'rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700'}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Búsqueda */}
      <input
        type="search" value={search} onChange={(e) => setSearch(e.target.value)}
        placeholder="Buscar por CIT, CPV, placa, OC, proveedor, transportista, guía o gate"
        aria-label="Buscar en la cola"
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
      />

      {/* Tabla */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
        {isError ? (
          <div className="p-4"><ErrorState message={errorMessage} /></div>
        ) : isLoading ? (
          <div className="p-4"><TableSkeleton /></div>
        ) : items.length === 0 ? (
          <div className="p-4"><EmptyState title="No hay registros para los filtros actuales" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50/60 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-2.5 text-left">CPV</th>
                  <th className="px-3 py-2.5 text-left">CIT</th>
                  <th className="px-3 py-2.5 text-left">Placa</th>
                  <th className="px-3 py-2.5 text-left">Proveedor</th>
                  <th className="px-3 py-2.5 text-left">Transportista</th>
                  <th className="px-3 py-2.5 text-left">Gate</th>
                  <th className="px-3 py-2.5 text-left">Estado</th>
                  <th className="px-3 py-2.5 text-left">Llegada</th>
                  <th className="px-3 py-2.5 text-left">Clasificación</th>
                  <th className="px-3 py-2.5 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/60">
                    <td className="px-3 py-2 font-mono text-xs">{c.cpv_code ?? '—'}</td>
                    <td className="px-3 py-2 font-mono text-xs">{c.cit_code ?? '—'}</td>
                    <td className="px-3 py-2 font-mono text-xs">{c.observed_plate ?? c.expected_plate ?? '—'}</td>
                    <td className="px-3 py-2 text-xs">{c.supplier_name ?? '—'}</td>
                    <td className="px-3 py-2 text-xs">{c.carrier_name ?? '—'}</td>
                    <td className="px-3 py-2 text-xs">{c.gate_name ?? '—'}</td>
                    <td className="px-3 py-2"><StatusPill tone="info">{checkInStatusLabel(c.status)}</StatusPill></td>
                    <td className="px-3 py-2 text-xs text-slate-500">{c.arrived_at ? new Date(c.arrived_at).toLocaleString('es-PE') : '—'}</td>
                    <td className="px-3 py-2 text-xs">{arrivalClassificationLabel(c.arrival_classification)}</td>
                    <td className="px-3 py-2 text-right">
                      <button type="button" onClick={() => navigate(`/logistics/inbound/gate-control/check-ins/${c.id}`)} className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50">Ver</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}