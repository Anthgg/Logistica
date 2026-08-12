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
import { gateCheckInsApi } from '../api/gateCheckInsApi'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import type { ReceptionAppointmentSummary, WarehouseGate } from '../types/gate-control'
import { GateCitQrScanner } from '../components/GateCitQrScanner'
import { EmptyState, ErrorState, StatusPill } from '../components/ui'
import { useDebouncedValue } from '../hooks/useDebouncedValue'

type Mode = 'qr' | 'cit' | 'search' | 'walkin'

export function CreateGateCheckInPage() {
  const navigate = useNavigate()
  const perms = useLogisticsPermissions()
  const canWalkIn = perms.hasPermission(LOGISTICS_PERMISSIONS.gateControl.createWalkIn)
  const walkInGuard = useSensitiveActionGuard({ permission: LOGISTICS_PERMISSIONS.gateControl.createWalkIn })

  const [mode, setMode] = useState<Mode>('cit')
  const [gates, setGates] = useState<WarehouseGate[]>([])
  const [gateId, setGateId] = useState('')
  const [citCode, setCitCode] = useState('')
  const [qrOpen, setQrOpen] = useState(false)
  const [resolved, setResolved] = useState<ReceptionAppointmentSummary | null>(null)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 350)
  const [searchResults, setSearchResults] = useState<ReceptionAppointmentSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Walk-in fields
  const [walkInPlate, setWalkInPlate] = useState('')
  const [walkInCarrierId, setWalkInCarrierId] = useState('')

  useEffect(() => {
    warehouseGatesApi.list({ status: 'ACTIVE', page: 1, page_size: 100 }).then((res) => {
      setGates(res.items ?? [])
      if (res.items && res.items.length > 0) setGateId(res.items[0]!.id)
    }).catch(() => setGates([]))
  }, [])

  const resolve = async (payload: { cit_code?: string; qr_payload?: string; plate?: string }) => {
    if (!gateId) { setError('Selecciona un gate.'); return }
    setLoading(true); setError(null)
    try {
      const appt = await gateCheckInsApi.resolveAppointment({ ...payload, warehouse_id: gates.find((g) => g.id === gateId)?.warehouse_id })
      if (!appt) { setError('No se encontró cita elegible.'); setResolved(null) }
      else setResolved(appt)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo resolver la cita.')
      setResolved(null)
    } finally {
      setLoading(false)
    }
  }

  // Búsqueda por placa/OC
  useEffect(() => {
    if (mode !== 'search' || !debouncedSearch.trim()) { setSearchResults([]); return }
    resolve({ plate: debouncedSearch }).then(() => {
      if (resolved) setSearchResults([resolved])
    }).catch(() => setSearchResults([]))
  }, [mode, debouncedSearch])

  const handleCreate = async () => {
    if (!gateId || !resolved) { setError('Resuelve una cita primero.'); return }
    setSubmitting(true); setError(null)
    try {
      const ci = await gateCheckInsApi.create({ gate_id: gateId, appointment_id: resolved.id })
      navigate(`/logistics/inbound/gate-control/check-ins/${ci.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el check-in.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleWalkIn = async () => {
    if (!gateId) { setError('Selecciona un gate.'); return }
    setSubmitting(true); setError(null)
    try {
      const executed = await walkInGuard.run(async () => {
        const ci = await gateCheckInsApi.createWalkIn({ gate_id: gateId, plate: walkInPlate || undefined, carrier_id: walkInCarrierId || undefined })
        navigate(`/logistics/inbound/gate-control/check-ins/${ci.id}`)
      })
      if (!executed) setSubmitting(false)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el walk-in.')
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">Nuevo check-in</h1>
        <button type="button" onClick={() => navigate('/logistics/inbound/gate-control')} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Volver</button>
      </div>

      {error && <ErrorState message={error} />}

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        <label htmlFor="gate" className="mb-1 block text-xs font-bold text-slate-700">Gate</label>
        <Select value={gateId} onValueChange={setGateId}>
          <SelectTrigger id="gate"><SelectValue placeholder="Selecciona un gate" /></SelectTrigger>
          <SelectContent>
            {gates.map((g) => <SelectItem key={g.id} value={g.id}>{g.code} — {g.name}</SelectItem>)}
          </SelectContent>
        </Select>
        <p className="mt-1 text-[11px] text-slate-500">No se solicita guardia. El backend lo obtiene de la sesión.</p>
      </div>

      <div role="tablist" className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/60 p-1">
        {([['cit', 'Código CIT'], ['qr', 'Escanear QR'], ['search', 'Buscar'], ['walkin', 'Sin cita']] as Array<[Mode, string]>).map(([key, label]) => (
          <button key={key} role="tab" aria-selected={mode === key} type="button" onClick={() => { setMode(key); setResolved(null); setError(null) }}
            className={mode === key ? 'rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-[#1F4E6D] shadow-xs' : 'rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700'}>
            {label}
          </button>
        ))}
      </div>

      {mode === 'cit' && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <label htmlFor="cit" className="mb-1 block text-xs font-bold text-slate-700">Código CIT</label>
          <input id="cit" value={citCode} onChange={(e) => setCitCode(e.target.value.toUpperCase())} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" autoComplete="off" />
          <button type="button" disabled={loading || !citCode.trim()} onClick={() => void resolve({ cit_code: citCode.trim() })} className="mt-2 rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
            {loading ? 'Resolviendo…' : 'Resolver cita'}
          </button>
        </div>
      )}

      {mode === 'qr' && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          {!qrOpen ? (
            <button type="button" onClick={() => setQrOpen(true)} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55]">Abrir escáner QR</button>
          ) : (
            <GateCitQrScanner onPayload={(p) => { setQrOpen(false); void resolve({ qr_payload: p }) }} onCancel={() => setQrOpen(false)} />
          )}
        </div>
      )}

      {mode === 'search' && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <label htmlFor="search-cit" className="mb-1 block text-xs font-bold text-slate-700">Buscar por placa u OC</label>
          <input id="search-cit" type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Placa o código OC" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          {searchResults.length > 0 && (
            <ul className="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-100 text-xs">
              {searchResults.map((a) => (
                <li key={a.id} className="flex items-center justify-between px-2 py-1.5">
                  <span>{a.cit_code} · {a.vehicle_plate ?? '—'} · {a.supplier_name ?? '—'}</span>
                  <button type="button" onClick={() => setResolved(a)} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold">Elegir</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {mode === 'walkin' && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <p className="mb-2 text-[11px] text-slate-500">Solo con capability. Requiere step-up.</p>
          {walkInGuard.isBlocked && <p className="text-amber-600">Se requiere verificación reforzada.</p>}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Placa (opcional)</label>
              <input value={walkInPlate} onChange={(e) => setWalkInPlate(e.target.value.toUpperCase())} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">ID transportista (opcional)</label>
              <input value={walkInCarrierId} onChange={(e) => setWalkInCarrierId(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
            </div>
          </div>
          {canWalkIn && (
            <button type="button" disabled={submitting || walkInGuard.isBlocked} onClick={() => void handleWalkIn()} className="mt-2 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
              {submitting ? 'Creando…' : 'Crear walk-in'}
            </button>
          )}
        </div>
      )}

      {/* Resumen de cita resuelta */}
      {resolved && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800">Cita resuelta</h2>
            {resolved.is_eligible ? <StatusPill tone="success">Elegible</StatusPill> : <StatusPill tone="danger">No elegible</StatusPill>}
          </div>
          <dl className="mt-2 grid grid-cols-2 gap-1 text-xs md:grid-cols-3">
            <dt className="text-slate-500">CIT:</dt><dd className="font-mono">{resolved.cit_code}</dd>
            <dt className="text-slate-500">Almacén:</dt><dd>{resolved.warehouse_name}</dd>
            <dt className="text-slate-500">Ventana:</dt><dd>{resolved.time_start} - {resolved.time_end}</dd>
            <dt className="text-slate-500">Proveedor:</dt><dd>{resolved.supplier_name ?? '—'}</dd>
            <dt className="text-slate-500">Placa esperada:</dt><dd className="font-mono">{resolved.vehicle_plate ?? '—'}</dd>
            <dt className="text-slate-500">Conductor:</dt><dd>{resolved.driver_name_redacted ?? '—'}</dd>
            <dt className="text-slate-500">Precinto:</dt><dd className="font-mono">{resolved.seal_number_expected ?? '—'}</dd>
          </dl>
          {resolved.warnings.length > 0 && (
            <ul className="mt-2 list-disc pl-4 text-xs text-amber-700">{resolved.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
          )}
          <button type="button" disabled={submitting || !resolved.is_eligible} onClick={() => void handleCreate()} className="mt-3 rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
            {submitting ? 'Creando…' : 'Crear check-in'}
          </button>
        </div>
      )}

      {!resolved && mode !== 'walkin' && !loading && !qrOpen && <EmptyState title="Resuelve una cita para continuar" />}
    </div>
  )
}