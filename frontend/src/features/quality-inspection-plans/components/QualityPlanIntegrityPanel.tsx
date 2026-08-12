import type { QualityPlanIntegrity } from '../types/quality-inspection-plans'

interface QualityPlanIntegrityPanelProps {
  integrity: QualityPlanIntegrity | null
}

const STATUS_CONFIG: Record<string, { label: string; tone: string }> = {
  VALID: { label: 'Válido', tone: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
  INVALID: { label: 'Inválido', tone: 'bg-rose-50 text-rose-700 border border-rose-200' },
  PENDING: { label: 'Pendiente', tone: 'bg-amber-50 text-amber-700 border border-amber-200' },
  NOT_VERIFIED: { label: 'Sin verificar', tone: 'bg-slate-100 text-slate-600' },
}

export function QualityPlanIntegrityPanel({ integrity }: QualityPlanIntegrityPanelProps) {
  if (!integrity) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
        <h2 className="text-sm font-bold text-slate-800">Integridad</h2>
        <p className="mt-2 text-slate-500">Sin información de integridad.</p>
      </div>
    )
  }

  const cfg = STATUS_CONFIG[integrity.status] ?? STATUS_CONFIG.NOT_VERIFIED

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800">Integridad</h2>
        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ${cfg.tone}`}>
          {cfg.label}
        </span>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-1 font-mono text-[11px]">
        <dt className="text-slate-500">Hash versión:</dt>
        <dd>{integrity.version_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash scopes:</dt>
        <dd>{integrity.scopes_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash controles:</dt>
        <dd>{integrity.controls_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash tolerancias:</dt>
        <dd>{integrity.tolerances_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash muestreo:</dt>
        <dd>{integrity.sampling_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash certificados:</dt>
        <dd>{integrity.certificates_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash condiciones:</dt>
        <dd>{integrity.conditions_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Hash snapshot:</dt>
        <dd>{integrity.snapshot_hash?.slice(0, 16) ?? '—'}</dd>
        <dt className="text-slate-500">Algoritmo:</dt>
        <dd>{integrity.algorithm ?? '—'}</dd>
        <dt className="text-slate-500">Última verificación:</dt>
        <dd>{integrity.last_verified_at ?? '—'}</dd>
      </dl>
    </div>
  )
}
