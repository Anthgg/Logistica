import type { GateCheckInHistoryEvent } from '../types/gate-control'
import { EmptyState } from './ui'

export function GateCheckInHistoryTimeline({ history }: { history: GateCheckInHistoryEvent[] }) {
  if (history.length === 0) return <EmptyState title="Sin eventos de historial" />
  return (
    <ol className="space-y-2 border-l border-slate-200 pl-4 text-xs">
      {history.map((e) => (
        <li key={e.id} className="relative">
          <span className="absolute -left-[21px] top-1 h-3 w-3 rounded-full border-2 border-[#1F4E6D] bg-white" />
          <div className="rounded-lg border border-slate-100 bg-white p-2.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800">{e.action}</span>
              <span className="text-[11px] text-slate-400">{new Date(e.occurred_at).toLocaleString('es-PE')}</span>
            </div>
            <dl className="mt-1 grid grid-cols-2 gap-x-2 gap-y-0.5 text-[11px] text-slate-500 md:grid-cols-3">
              <dt>Actor:</dt><dd>{e.actor_display_name ?? '—'}</dd>
              <dt>Actor efectivo:</dt><dd>{e.effective_actor_display_name ?? '—'}</dd>
              <dt>Estado anterior:</dt><dd>{e.previous_state ?? '—'}</dd>
              <dt>Estado nuevo:</dt><dd>{e.new_state ?? '—'}</dd>
              <dt>Motivo:</dt><dd>{e.reason ?? '—'}</dd>
              <dt>Resultado:</dt><dd>{e.result}</dd>
            </dl>
          </div>
        </li>
      ))}
    </ol>
  )
}