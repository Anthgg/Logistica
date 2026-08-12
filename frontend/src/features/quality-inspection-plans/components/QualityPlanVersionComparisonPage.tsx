import { useQuery } from '../../../features/inbound-docks/hooks/useQuery'
import type {
  QualityInspectionPlanVersion,
  QualityPlanScope,
  QualityControlDefinition,
} from '../types/quality-inspection-plans'

interface QualityPlanVersionComparisonPageProps {
  planId: string
  versionA: string
  versionB: string
}

interface VersionDetail {
  version: QualityInspectionPlanVersion
  scopes: QualityPlanScope[]
  controls: QualityControlDefinition[]
}

function DiffRow({
  label,
  valueA,
  valueB,
}: {
  label: string
  valueA: string | number | null
  valueB: string | number | null
}) {
  const isChanged = String(valueA ?? '—') !== String(valueB ?? '—')
  return (
    <tr className={isChanged ? 'bg-amber-50/60' : ''}>
      <td className="py-1 pr-2 text-[11px] font-medium text-slate-500">{label}</td>
      <td className="py-1 pr-2 text-[11px] text-slate-700">{valueA ?? '—'}</td>
      <td className="py-1 text-[11px] text-slate-700">{valueB ?? '—'}</td>
    </tr>
  )
}

function ControlDiff({
  controlsA,
  controlsB,
}: {
  controlsA: QualityControlDefinition[]
  controlsB: QualityControlDefinition[]
}) {
  const mapA = new Map(controlsA.map((c) => [c.control_id, c]))
  const mapB = new Map(controlsB.map((c) => [c.control_id, c]))

  const added = controlsB.filter((c) => !mapA.has(c.control_id))
  const removed = controlsA.filter((c) => !mapB.has(c.control_id))
  const modified = controlsB.filter((c) => {
    const prev = mapA.get(c.control_id)
    if (!prev) return false
    return (
      prev.name !== c.name ||
      prev.control_type !== c.control_type ||
      prev.required !== c.required ||
      prev.blocking_future !== c.blocking_future ||
      prev.evidence_required !== c.evidence_required ||
      prev.tolerance_id !== c.tolerance_id ||
      prev.sampling_plan_id !== c.sampling_plan_id ||
      prev.certificate_requirement_id !== c.certificate_requirement_id
    )
  })

  if (added.length === 0 && removed.length === 0 && modified.length === 0) {
    return <p className="text-[11px] text-slate-500">Sin cambios en controles.</p>
  }

  return (
    <div className="space-y-2">
      {added.length > 0 && (
        <div>
          <h4 className="text-[11px] font-semibold text-emerald-700">Agregados ({added.length})</h4>
          <ul className="list-disc pl-4 text-[11px] text-slate-600">
            {added.map((c) => (
              <li key={c.control_id}>{c.name} ({c.control_type})</li>
            ))}
          </ul>
        </div>
      )}
      {removed.length > 0 && (
        <div>
          <h4 className="text-[11px] font-semibold text-rose-700">Eliminados ({removed.length})</h4>
          <ul className="list-disc pl-4 text-[11px] text-slate-600">
            {removed.map((c) => (
              <li key={c.control_id}>{c.name} ({c.control_type})</li>
            ))}
          </ul>
        </div>
      )}
      {modified.length > 0 && (
        <div>
          <h4 className="text-[11px] font-semibold text-amber-700">Modificados ({modified.length})</h4>
          <ul className="list-disc pl-4 text-[11px] text-slate-600">
            {modified.map((c) => (
              <li key={c.control_id}>{c.name} ({c.control_type})</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export function QualityPlanVersionComparisonPage({
  planId,
  versionA,
  versionB,
}: QualityPlanVersionComparisonPageProps) {
  const { data: detailA, isLoading: loadingA, isError: errorA } = useQuery<VersionDetail>(
    ['quality-plan-version-detail', planId, versionA],
    `/logistics/quality-inspection-plans/${planId}/versions/${versionA}`,
  )

  const { data: detailB, isLoading: loadingB, isError: errorB } = useQuery<VersionDetail>(
    ['quality-plan-version-detail', planId, versionB],
    `/logistics/quality-inspection-plans/${planId}/versions/${versionB}`,
  )

  if (loadingA || loadingB) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-500">
        Cargando versiones para comparar…
      </div>
    )
  }

  if (errorA || errorB || !detailA || !detailB) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-600">
        No se pudieron cargar las versiones.
      </div>
    )
  }

  const vA = detailA.version
  const vB = detailB.version

  return (
    <div className="space-y-4 text-xs">
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-bold text-slate-800">
          Comparación: v{vA.version_number} vs v{vB.version_number}
        </h2>
        <p className="mb-3 text-[11px] text-slate-500">
          Resaltado en amarillo indica diferencias entre las versiones.
        </p>

        <h3 className="mb-1 font-semibold text-slate-700">Información general</h3>
        <table className="w-full text-left">
          <tbody>
            <DiffRow label="Versión" valueA={vA.version_number} valueB={vB.version_number} />
            <DiffRow label="Estado" valueA={vA.status} valueB={vB.status} />
            <DiffRow label="Prioridad" valueA={vA.priority} valueB={vB.priority} />
            <DiffRow label="Vigente desde" valueA={vA.valid_from} valueB={vB.valid_from} />
            <DiffRow label="Vigente hasta" valueA={vA.valid_until} valueB={vB.valid_until} />
            <DiffRow label="Scopes" valueA={vA.scope_count} valueB={vB.scope_count} />
            <DiffRow label="Controles" valueA={vA.control_count} valueB={vB.control_count} />
            <DiffRow label="Tolerancias" valueA={vA.tolerance_count} valueB={vB.tolerance_count} />
            <DiffRow label="Muestreos" valueA={vA.sampling_count} valueB={vB.sampling_count} />
            <DiffRow label="Certificados" valueA={vA.certificate_count} valueB={vB.certificate_count} />
            <DiffRow label="Conflictos" valueA={vA.conflict_count} valueB={vB.conflict_count} />
            <DiffRow label="Validación" valueA={vA.validation_status} valueB={vB.validation_status} />
          </tbody>
        </table>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="mb-2 font-semibold text-slate-700">Controles</h3>
        <ControlDiff controlsA={detailA.controls} controlsB={detailB.controls} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="mb-1 font-semibold text-slate-700">Scopes</h3>
        <table className="w-full text-left">
          <tbody>
            <DiffRow
              label="Cantidad de scopes"
              valueA={detailA.scopes.length}
              valueB={detailB.scopes.length}
            />
          </tbody>
        </table>
        <ul className="mt-1 space-y-0.5">
          {detailA.scopes.map((s) => (
            <li key={s.scope_id} className="text-[11px] text-slate-600">
              <span className="font-mono text-slate-400">A:</span> {s.scope_type} — {s.product_name ?? s.category_name ?? s.scope_id} ({s.action})
            </li>
          ))}
          {detailB.scopes.map((s) => (
            <li key={s.scope_id} className="text-[11px] text-slate-600">
              <span className="font-mono text-slate-400">B:</span> {s.scope_type} — {s.product_name ?? s.category_name ?? s.scope_id} ({s.action})
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="mb-1 font-semibold text-slate-700">Hash</h3>
        <dl className="grid grid-cols-2 gap-1 font-mono text-[11px] md:grid-cols-4">
          <dt className="text-slate-500">Hash vA:</dt>
          <dd>{vA.hash?.slice(0, 16) ?? '—'}</dd>
          <dt className="text-slate-500">Hash vB:</dt>
          <dd>{vB.hash?.slice(0, 16) ?? '—'}</dd>
          <dt className="text-slate-500">Coinciden:</dt>
          <dd className={vA.hash === vB.hash ? 'text-emerald-600' : 'text-rose-600'}>
            {vA.hash === vB.hash ? 'Sí' : 'No'}
          </dd>
        </dl>
      </div>
    </div>
  )
}
