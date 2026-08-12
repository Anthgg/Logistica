import { useState } from 'react'
import { supplierEvaluationTemplatesApi } from '../api/supplierEvaluationTemplatesApi'
import type {
  EvaluationTemplateVersionCreate,
  SupplierEvaluationTemplateVersion,
} from '../types/evaluation'
import { ErrorState, StatusPill } from './ui/SharedState'
import { Modal } from './ui/Overlay'

const TIE_POLICIES = ['HIGHEST_TECHNICAL', 'LOWEST_PRICE', 'LOWEST_RISK', 'SHORTEST_DELIVERY', 'MANUAL', 'REQUOTE'] as const
const AWARD_POLICIES = ['SINGLE', 'SPLIT_BY_LINE', 'SPLIT_BY_QUANTITY', 'NO_AWARD', 'REQUOTE'] as const
const MISSING_POLICIES = ['ZERO', 'EXCLUDE', 'MINIMUM', 'REQUIRE', 'PENALTY'] as const

export function EvaluationTemplateVersionsPanel({
  templateId,
  versions,
  canManage,
  onChanged,
}: {
  templateId: string
  versions: SupplierEvaluationTemplateVersion[]
  canManage: boolean
  onChanged: () => void
}) {
  const [createOpen, setCreateOpen] = useState(false)
  const [compareA, setCompareA] = useState<string>('')
  const [compareB, setCompareB] = useState<string>('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<EvaluationTemplateVersionCreate>({
    version: '',
    scale: '100',
    missing_data_policy: 'ZERO',
    tie_policy: 'HIGHEST_TECHNICAL',
    award_policy: 'SINGLE',
    comparison_currency: null,
  })

  const handleCreate = async () => {
    if (!form.version.trim()) {
      setError('La versión es obligatoria.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await supplierEvaluationTemplatesApi.createVersion(templateId, form)
      setCreateOpen(false)
      setForm({ ...form, version: '' })
      onChanged()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo crear la versión.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleActivate = async (versionId: string) => {
    if (!confirm('¿Activar esta versión? Reemplazará a la versión activa actual.')) return
    try {
      await supplierEvaluationTemplatesApi.activateVersion(templateId, versionId)
      onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo activar.')
    }
  }

  const handleValidate = async (versionId: string) => {
    try {
      await supplierEvaluationTemplatesApi.validateVersion(templateId, versionId)
      onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo validar.')
    }
  }

  const handleRetire = async (versionId: string) => {
    if (!confirm('¿Retirar esta versión?')) return
    try {
      await supplierEvaluationTemplatesApi.retireVersion(templateId, versionId)
      onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo retirar.')
    }
  }

  return (
    <div className="space-y-3">
      {error && <ErrorState message={error} />}

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800">
          {versions.length} versión(es)
        </h2>
        {canManage && (
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Nueva versión
          </button>
        )}
      </div>

      {/* Comparador simple */}
      {versions.length >= 2 && (
        <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-3 text-xs">
          <div className="mb-2 font-semibold text-indigo-800">Comparar versiones</div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              aria-label="Versión A"
              value={compareA}
              onChange={(e) => setCompareA(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-1 text-xs"
            >
              <option value="">Versión A…</option>
              {versions.map((v) => (
                <option key={v.id} value={v.id}>{v.version}</option>
              ))}
            </select>
            <select
              aria-label="Versión B"
              value={compareB}
              onChange={(e) => setCompareB(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-1 text-xs"
            >
              <option value="">Versión B…</option>
              {versions.map((v) => (
                <option key={v.id} value={v.id}>{v.version}</option>
              ))}
            </select>
            <CompareVersions
              a={versions.find((v) => v.id === compareA) ?? null}
              b={versions.find((v) => v.id === compareB) ?? null}
            />
          </div>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50/60 text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2.5 text-left">Versión</th>
              <th className="px-3 py-2.5 text-left">Estado</th>
              <th className="px-3 py-2.5 text-left">Escala</th>
              <th className="px-3 py-2.5 text-left">Puntaje mín.</th>
              <th className="px-3 py-2.5 text-left">Datos faltantes</th>
              <th className="px-3 py-2.5 text-left">Empate</th>
              <th className="px-3 py-2.5 text-left">Adjudicación</th>
              <th className="px-3 py-2.5 text-left">Moneda</th>
              <th className="px-3 py-2.5 text-left">Motor</th>
              <th className="px-3 py-2.5 text-left">Hash</th>
              <th className="px-3 py-2.5 text-left">Vigencia</th>
              <th className="px-3 py-2.5 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {versions.map((v) => (
              <tr key={v.id} className="hover:bg-slate-50/60">
                <td className="px-3 py-2 font-mono text-xs">{v.version}</td>
                <td className="px-3 py-2">
                  <StatusPill tone={versionTone(v.status)}>{v.status}</StatusPill>
                </td>
                <td className="px-3 py-2 text-xs">{v.scale}</td>
                <td className="px-3 py-2 text-xs font-mono">{v.min_total_score ?? '—'}</td>
                <td className="px-3 py-2 text-xs">{v.missing_data_policy}</td>
                <td className="px-3 py-2 text-xs">{v.tie_policy}</td>
                <td className="px-3 py-2 text-xs">{v.award_policy}</td>
                <td className="px-3 py-2 text-xs">{v.comparison_currency ?? '—'}</td>
                <td className="px-3 py-2 text-xs font-mono">{v.engine}</td>
                <td className="px-3 py-2 text-xs font-mono text-slate-500" title={v.partial_hash}>
                  {v.partial_hash.slice(0, 10)}…
                </td>
                <td className="px-3 py-2 text-xs text-slate-500">
                  {v.effective_from ? new Date(v.effective_from).toLocaleDateString('es-PE') : '—'}
                </td>
                <td className="px-3 py-2 text-right">
                  <div className="flex flex-wrap justify-end gap-1">
                    {canManage && v.status === 'DRAFT' && (
                      <button
                        type="button"
                        onClick={() => void handleValidate(v.id)}
                        className="rounded-lg border border-slate-200 px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Validar
                      </button>
                    )}
                    {canManage && v.status !== 'ACTIVE' && v.status !== 'ARCHIVED' && (
                      <button
                        type="button"
                        onClick={() => void handleActivate(v.id)}
                        className="rounded-lg border border-emerald-200 px-2 py-1 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50"
                      >
                        Activar
                      </button>
                    )}
                    {canManage && (v.status === 'ACTIVE' || v.status === 'VALIDATED') && (
                      <button
                        type="button"
                        onClick={() => void handleRetire(v.id)}
                        className="rounded-lg border border-amber-200 px-2 py-1 text-[11px] font-semibold text-amber-700 hover:bg-amber-50"
                      >
                        Retirar
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Nueva versión"
        size="md"
        footer={
          <>
            <button
              type="button"
              onClick={() => setCreateOpen(false)}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={handleCreate}
              className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
            >
              {submitting ? 'Creando…' : 'Crear versión'}
            </button>
          </>
        }
      >
        <div className="space-y-3">
          {error && (
            <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
              {error}
            </p>
          )}
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Versión</label>
            <input
              value={form.version}
              onChange={(e) => setForm({ ...form, version: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Escala</label>
              <input
                value={form.scale}
                onChange={(e) => setForm({ ...form, scale: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Moneda comparación</label>
              <input
                value={form.comparison_currency ?? ''}
                onChange={(e) => setForm({ ...form, comparison_currency: e.target.value || null })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Datos faltantes</label>
              <select
                value={form.missing_data_policy}
                onChange={(e) => setForm({ ...form, missing_data_policy: e.target.value as EvaluationTemplateVersionCreate['missing_data_policy'] })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {MISSING_POLICIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Política de empate</label>
              <select
                value={form.tie_policy}
                onChange={(e) => setForm({ ...form, tie_policy: e.target.value as EvaluationTemplateVersionCreate['tie_policy'] })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {TIE_POLICIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Política de adjudicación</label>
            <select
              value={form.award_policy}
              onChange={(e) => setForm({ ...form, award_policy: e.target.value as EvaluationTemplateVersionCreate['award_policy'] })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {AWARD_POLICIES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
      </Modal>
    </div>
  )
}

function CompareVersions({
  a,
  b,
}: {
  a: SupplierEvaluationTemplateVersion | null
  b: SupplierEvaluationTemplateVersion | null
}) {
  if (!a || !b) return <span className="text-xs text-slate-400">Selecciona dos versiones</span>
  const fields: Array<keyof SupplierEvaluationTemplateVersion> = [
    'scale',
    'min_total_score',
    'missing_data_policy',
    'tie_policy',
    'award_policy',
    'comparison_currency',
    'engine',
  ]
  return (
    <div className="mt-2 w-full overflow-x-auto rounded-lg border border-slate-200 bg-white text-xs">
      <table className="min-w-full divide-y divide-slate-100">
        <thead className="bg-slate-50 text-slate-500">
          <tr>
            <th className="px-2 py-1 text-left">Campo</th>
            <th className="px-2 py-1 text-left">{a.version}</th>
            <th className="px-2 py-1 text-left">{b.version}</th>
          </tr>
        </thead>
        <tbody>
          {fields.map((f) => {
            const va = String(a[f] ?? '—')
            const vb = String(b[f] ?? '—')
            const diff = va !== vb
            return (
              <tr key={f} className={diff ? 'bg-amber-50/50' : ''}>
                <td className="px-2 py-1 font-mono">{f}</td>
                <td className="px-2 py-1">{va}</td>
                <td className="px-2 py-1">{vb}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function versionTone(status: SupplierEvaluationTemplateVersion['status']): 'success' | 'warning' | 'muted' | 'info' {
  switch (status) {
    case 'ACTIVE':
      return 'success'
    case 'VALIDATED':
      return 'info'
    case 'RETIRED':
    case 'ARCHIVED':
      return 'muted'
    default:
      return 'warning'
  }
}