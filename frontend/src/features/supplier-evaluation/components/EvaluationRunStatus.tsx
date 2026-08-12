import { useEffect, useRef, useState } from 'react'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import type { QuotationEvaluationRun } from '../types/evaluation'
import { StatusPill } from './ui/SharedState'

const POLL_MS = 3000

export function EvaluationRunStatus({ evaluationId }: { evaluationId: string }) {
  const [runs, setRuns] = useState<QuotationEvaluationRun[]>([])
  const timerRef = useRef<number | null>(null)

  const load = async () => {
    try {
      const list = await quotationEvaluationsApi.listRuns(evaluationId)
      setRuns(list)
      const active = list.some((r) => r.status === 'QUEUED' || r.status === 'RUNNING')
      if (active && timerRef.current === null) {
        timerRef.current = window.setInterval(() => void load(), POLL_MS)
      } else if (!active && timerRef.current !== null) {
        window.clearInterval(timerRef.current)
        timerRef.current = null
      }
    } catch {
      // noop
    }
  }

  useEffect(() => {
    void load()
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evaluationId])

  if (runs.length === 0) return <p className="text-xs text-slate-500">Sin corridas registradas.</p>

  return (
    <div className="space-y-2">
      <h2 className="text-sm font-bold text-slate-800">Corridas de cálculo</h2>
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-xs">
          <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2.5 text-left">N.º</th>
              <th className="px-3 py-2.5 text-left">Estado</th>
              <th className="px-3 py-2.5 text-left">Motor</th>
              <th className="px-3 py-2.5 text-left">Inicio</th>
              <th className="px-3 py-2.5 text-left">Fin</th>
              <th className="px-3 py-2.5 text-right">Candidatos</th>
              <th className="px-3 py-2.5 text-left">Input hash</th>
              <th className="px-3 py-2.5 text-left">Output hash</th>
              <th className="px-3 py-2.5 text-left">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {runs.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50/60">
                <td className="px-3 py-2 font-mono">{r.run_number}</td>
                <td className="px-3 py-2"><RunStatusPill status={r.status} /></td>
                <td className="px-3 py-2 font-mono">{r.engine}</td>
                <td className="px-3 py-2">{r.started_at ?? '—'}</td>
                <td className="px-3 py-2">{r.finished_at ?? '—'}</td>
                <td className="px-3 py-2 text-right font-mono">{r.candidates_count}</td>
                <td className="px-3 py-2 font-mono text-[11px] text-slate-500" title={r.input_partial_hash ?? ''}>{r.input_partial_hash?.slice(0, 10) ?? '—'}…</td>
                <td className="px-3 py-2 font-mono text-[11px] text-slate-500" title={r.output_partial_hash ?? ''}>{r.output_partial_hash?.slice(0, 10) ?? '—'}…</td>
                <td className="px-3 py-2">{r.error_message ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function RunStatusPill({ status }: { status: QuotationEvaluationRun['status'] }) {
  const tone = status === 'COMPLETED' ? 'success' : status === 'FAILED' ? 'danger' : status === 'SUPERSEDED' ? 'muted' : 'info'
  return <StatusPill tone={tone}>{status}</StatusPill>
}