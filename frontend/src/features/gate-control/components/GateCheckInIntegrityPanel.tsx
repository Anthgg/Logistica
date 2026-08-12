import type { GateIntegrityStatus } from '../types/gate-control'
import { EmptyState, StatusPill } from './ui'

export function GateCheckInIntegrityPanel({ integrity }: { integrity: GateIntegrityStatus | null }) {
  if (!integrity) return <EmptyState title="Sin información de integridad" />
  const tone = integrity.status === 'VERIFIED' ? 'success' : integrity.status === 'MISMATCH' ? 'danger' : integrity.status === 'INCOMPLETE' ? 'warning' : 'muted'
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800">Integridad</h2>
        <StatusPill tone={tone}>{integrity.status === 'VERIFIED' ? 'Integridad verificada' : integrity.status === 'MISMATCH' ? 'Hash no coincide' : integrity.status === 'INCOMPLETE' ? 'Inconclusa' : 'No verificada'}</StatusPill>
      </div>
      <dl className="mt-2 grid grid-cols-2 gap-1 font-mono text-[11px]">
        <dt className="text-slate-500">Hash revisión:</dt><dd>{integrity.revision_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash checklist:</dt><dd>{integrity.checklist_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash evidencias:</dt><dd>{integrity.evidence_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash decisión:</dt><dd>{integrity.decision_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash snapshot:</dt><dd>{integrity.snapshot_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash CPV:</dt><dd>{integrity.cpv_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Algoritmo:</dt><dd>{integrity.algorithm ?? '—'}</dd>
        <dt className="text-slate-500">Última verificación:</dt><dd>{integrity.last_verified_at ?? '—'}</dd>
      </dl>
      <p className="mt-2 text-[11px] text-slate-500">No se llama firma digital a SHA-256.</p>
    </div>
  )
}