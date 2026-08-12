import { useCallback, useEffect, useState } from 'react'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import type {
  EvaluationExchangeRateSnapshot,
  EvaluationExchangeRateInput,
} from '../types/evaluation'
import { ErrorState, StatusPill, TableSkeleton } from './ui/SharedState'
import { Modal } from './ui/Overlay'
import { DecimalInput } from './ui/DecimalInput'

export function EvaluationCurrencySection({
  evaluationId,
}: {
  evaluationId: string
}) {
  const [rates, setRates] = useState<EvaluationExchangeRateSnapshot[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<EvaluationExchangeRateInput>({
    from_currency: '',
    to_currency: '',
    rate: '',
    source: '',
    rate_date: '',
  })
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setRates(await quotationEvaluationsApi.listExchangeRates(evaluationId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudieron cargar las tasas.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  const handleRegister = async () => {
    if (!form.from_currency.trim() || !form.to_currency.trim() || !form.rate.trim() || !form.source.trim() || !form.rate_date.trim()) {
      alert('Tasa, fuente y fecha son obligatorios.')
      return
    }
    setSubmitting(true)
    try {
      await quotationEvaluationsApi.registerExchangeRate(evaluationId, form)
      setOpen(false)
      setForm({ from_currency: '', to_currency: '', rate: '', source: '', rate_date: '' })
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo registrar la tasa.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleApprove = async (rateId: string) => {
    try {
      await quotationEvaluationsApi.approveExchangeRate(evaluationId, rateId)
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo aprobar.')
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800">Tasas registradas</h2>
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          Registrar tasa
        </button>
      </div>

      <p className="rounded-lg border border-amber-100 bg-amber-50/50 px-3 py-2 text-xs text-amber-800">
        No se consulta tipo de cambio desde React. La conversión autoritativa la
        realiza el backend. No se acepta una tasa sin fuente y fecha.
      </p>

      {rates.length === 0 ? (
        <p className="text-xs text-slate-500">No hay tasas registradas.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">De</th>
                <th className="px-3 py-2.5 text-left">A</th>
                <th className="px-3 py-2.5 text-right">Tasa</th>
                <th className="px-3 py-2.5 text-left">Fuente</th>
                <th className="px-3 py-2.5 text-left">Fecha</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rates.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2 font-mono">{r.from_currency}</td>
                  <td className="px-3 py-2 font-mono">{r.to_currency}</td>
                  <td className="px-3 py-2 text-right font-mono">{r.rate}</td>
                  <td className="px-3 py-2">{r.source}</td>
                  <td className="px-3 py-2">{r.rate_date}</td>
                  <td className="px-3 py-2">
                    {r.is_approved ? (
                      <StatusPill tone="success">Aprobada</StatusPill>
                    ) : (
                      <StatusPill tone="warning">Pendiente</StatusPill>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {!r.is_approved && (
                      <button
                        type="button"
                        onClick={() => void handleApprove(r.id)}
                        className="rounded-lg border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50"
                      >
                        Aprobar
                      </button>
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
        title="Registrar tasa de cambio"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleRegister} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Guardando…' : 'Registrar'}</button>
          </>
        }
      >
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">De (moneda)</label>
            <input value={form.from_currency} onChange={(e) => setForm({ ...form, from_currency: e.target.value.toUpperCase() })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">A (moneda)</label>
            <input value={form.to_currency} onChange={(e) => setForm({ ...form, to_currency: e.target.value.toUpperCase() })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
          </div>
          <DecimalInput label="Tasa" value={form.rate} onChange={(v) => setForm({ ...form, rate: v })} maxDecimals={6} />
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Fuente</label>
            <input value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Fecha</label>
            <input type="date" value={form.rate_date} onChange={(e) => setForm({ ...form, rate_date: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
        </div>
      </Modal>
    </div>
  )
}