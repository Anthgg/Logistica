import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { supplierEvaluationTemplatesApi } from '../api/supplierEvaluationTemplatesApi'
import type {
  EvaluationCriterionCreate,
  EvaluationCriterionDefinition,
  EvaluationCriterionGroup,
  EvaluationCriterionUpdate,
  EvaluationScoringMethod,
  SupplierEvaluationTemplateVersion,
} from '../types/evaluation'
import { criterionGroupLabel, isDecimalString } from '../format'
import { Modal } from './ui/Overlay'
import { DecimalInput } from './ui/DecimalInput'

const GROUPS: EvaluationCriterionGroup[] = ['ECONOMIC', 'TECHNICAL', 'COMMERCIAL', 'RISK', 'QUALITY', 'COMPLIANCE', 'OTHER']
const METHODS: EvaluationScoringMethod[] = ['PRICE', 'TECHNICAL', 'MANUAL', 'COMPLIANCE', 'RISK', 'QUALITY', 'DELIVERY', 'DOCUMENTATION', 'FORMULA']
const SOURCE_TYPES = ['RESPONSE_FIELD', 'RESPONSE_LINE', 'MANUAL', 'TECHNICAL_ASSESSMENT', 'COMPLIANCE', 'RISK_SNAPSHOT', 'QUALITY_SNAPSHOT'] as const

export function EvaluationCriteriaEditor({
  templateId,
  version,
  criteria,
  canManage,
  onChanged,
}: {
  templateId: string
  version: SupplierEvaluationTemplateVersion
  criteria: EvaluationCriterionDefinition[]
  canManage: boolean
  onChanged: () => void
}) {
  const [editing, setEditing] = useState<EvaluationCriterionDefinition | null>(null)
  const [creating, setCreating] = useState(false)
  const [error] = useState<string | null>(null)

  const isLocked = version.status !== 'DRAFT'
  const readOnly = isLocked || !canManage

  const handleReorder = async (id: string, dir: -1 | 1) => {
    if (readOnly) return
    const ordered = criteria.toSorted((a, b) => a.order - b.order)
    const idx = ordered.findIndex((c) => c.id === id)
    const target = idx + dir
    if (target < 0 || target >= ordered.length) return
    ;[ordered[idx], ordered[target]] = [ordered[target], ordered[idx]]
    try {
      await supplierEvaluationTemplatesApi.reorderCriteria(
        templateId,
        version.id,
        ordered.map((c) => c.id),
      )
      onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo reordenar.')
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          {readOnly
            ? 'Versión no editable (estado: ' + version.status + ').'
            : 'Reordena con los botones o arrastrando. Los pesos se validan en otra pestaña.'}
        </p>
        {!readOnly && (
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Añadir criterio
          </button>
        )}
      </div>

      {error && (
        <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50/60 text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th className="px-2 py-2.5 text-left">Orden</th>
              <th className="px-3 py-2.5 text-left">Código</th>
              <th className="px-3 py-2.5 text-left">Nombre</th>
              <th className="px-3 py-2.5 text-left">Grupo</th>
              <th className="px-3 py-2.5 text-left">Método</th>
              <th className="px-3 py-2.5 text-right">Peso</th>
              <th className="px-3 py-2.5 text-center">Oblig.</th>
              <th className="px-3 py-2.5 text-center">Elimin.</th>
              <th className="px-3 py-2.5 text-right">Puntaje mín.</th>
              <th className="px-3 py-2.5 text-left">Fuente</th>
              <th className="px-3 py-2.5 text-center">Evidencia</th>
              <th className="px-3 py-2.5 text-left">Rúbrica</th>
              <th className="px-3 py-2.5 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {criteria.map((c, i) => (
              <tr key={c.id} className="hover:bg-slate-50/60">
                <td className="px-2 py-2 text-xs">
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      disabled={readOnly || i === 0}
                      onClick={() => void handleReorder(c.id, -1)}
                      aria-label="Subir criterio"
                      className="rounded border border-slate-200 px-1.5 py-0.5 text-slate-500 hover:bg-slate-100 disabled:opacity-40"
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      disabled={readOnly || i === criteria.length - 1}
                      onClick={() => void handleReorder(c.id, 1)}
                      aria-label="Bajar criterio"
                      className="rounded border border-slate-200 px-1.5 py-0.5 text-slate-500 hover:bg-slate-100 disabled:opacity-40"
                    >
                      ↓
                    </button>
                    <span className="ml-1 font-mono">{c.order}</span>
                  </div>
                </td>
                <td className="px-3 py-2 font-mono text-xs">{c.code}</td>
                <td className="px-3 py-2 text-xs">{c.name}</td>
                <td className="px-3 py-2 text-xs">{criterionGroupLabel(c.group)}</td>
                <td className="px-3 py-2 text-xs">{c.method}</td>
                <td className="px-3 py-2 text-right font-mono text-xs">{c.weight}</td>
                <td className="px-3 py-2 text-center text-xs">{c.is_required ? 'Sí' : '—'}</td>
                <td className="px-3 py-2 text-center text-xs">
                  {c.is_eliminator ? <span className="text-rose-600 font-semibold">Sí</span> : '—'}
                </td>
                <td className="px-3 py-2 text-right font-mono text-xs">{c.min_score ?? '—'}</td>
                <td className="px-3 py-2 text-xs">{c.source_type}</td>
                <td className="px-3 py-2 text-center text-xs">{c.evidence_required ? 'Sí' : '—'}</td>
                <td className="px-3 py-2 text-xs">
                  {c.rubric ? <span className="font-mono">{c.rubric.code}</span> : '—'}
                </td>
                <td className="px-3 py-2 text-right">
                  <div className="flex justify-end gap-1">
                    {!readOnly && (
                      <button
                        type="button"
                        onClick={() => setEditing(c)}
                        className="rounded-lg border border-slate-200 px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Editar
                      </button>
                    )}
                    {!readOnly && (
                      <button
                        type="button"
                        onClick={async () => {
                          if (!confirm('¿Desactivar este criterio?')) return
                          try {
                            await supplierEvaluationTemplatesApi.deactivateCriterion(templateId, version.id, c.id)
                            onChanged()
                          } catch (e) {
                            alert(e instanceof Error ? e.message : 'No se pudo desactivar.')
                          }
                        }}
                        className="rounded-lg border border-rose-200 px-2 py-1 text-[11px] font-semibold text-rose-700 hover:bg-rose-50"
                      >
                        Desactivar
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(creating || editing) && (
        <CriterionFormDialog
          templateId={templateId}
          versionId={version.id}
          criterion={editing}
          onClose={() => {
            setCreating(false)
            setEditing(null)
          }}
          onSaved={() => {
            setCreating(false)
            setEditing(null)
            onChanged()
          }}
        />
      )}
    </div>
  )
}

function CriterionFormDialog({
  templateId,
  versionId,
  criterion,
  onClose,
  onSaved,
}: {
  templateId: string
  versionId: string
  criterion: EvaluationCriterionDefinition | null
  onClose: () => void
  onSaved: () => void
}) {
  const [form, setForm] = useState<EvaluationCriterionCreate & EvaluationCriterionUpdate>({
    code: criterion?.code ?? '',
    name: criterion?.name ?? '',
    group: criterion?.group ?? 'TECHNICAL',
    method: criterion?.method ?? 'MANUAL',
    weight: criterion?.weight ?? '0',
    is_required: criterion?.is_required ?? false,
    is_eliminator: criterion?.is_eliminator ?? false,
    min_score: criterion?.min_score ?? null,
    source_type: criterion?.source_type ?? 'MANUAL',
    source_field: criterion?.source_field ?? null,
    evidence_required: criterion?.evidence_required ?? false,
    rubric_id: criterion?.rubric_id ?? null,
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const weightValid = isDecimalString(form.weight)

  const handleSubmit = async () => {
    if (!form.code.trim() || !form.name.trim()) {
      setError('Código y nombre son obligatorios.')
      return
    }
    if (!weightValid) {
      setError('El peso debe ser un número decimal válido.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      if (criterion) {
        await supplierEvaluationTemplatesApi.updateCriterion(templateId, versionId, criterion.id, form)
      } else {
        await supplierEvaluationTemplatesApi.createCriterion(templateId, versionId, form as EvaluationCriterionCreate)
      }
      onSaved()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el criterio.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open
      onOpenChange={(o) => !o && onClose()}
      title={criterion ? 'Editar criterio' : 'Nuevo criterio'}
      size="lg"
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={handleSubmit}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            {submitting ? 'Guardando…' : 'Guardar'}
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
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Código</label>
            <input
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Nombre</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Grupo</label>
            <Select value={form.group} onValueChange={(v) => setForm({ ...form, group: v as EvaluationCriterionGroup })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {GROUPS.map((g) => <SelectItem key={g} value={g}>{criterionGroupLabel(g)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Método</label>
            <Select value={form.method} onValueChange={(v) => setForm({ ...form, method: v as EvaluationScoringMethod })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {METHODS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <DecimalInput
            label="Peso"
            value={form.weight}
            onChange={(v) => setForm({ ...form, weight: v })}
            invalid={!weightValid}
            maxDecimals={4}
          />
          <DecimalInput
            label="Puntaje mínimo"
            value={form.min_score ?? ''}
            onChange={(v) => setForm({ ...form, min_score: v || null })}
            maxDecimals={4}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Fuente</label>
            <Select value={form.source_type ?? 'MANUAL'} onValueChange={(v) => setForm({ ...form, source_type: v as EvaluationCriterionCreate['source_type'] })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {SOURCE_TYPES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Campo fuente</label>
            <input
              value={form.source_field ?? ''}
              onChange={(e) => setForm({ ...form, source_field: e.target.value || null })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-4">
          <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
            <input
              type="checkbox"
              checked={form.is_required ?? false}
              onChange={(e) => setForm({ ...form, is_required: e.target.checked })}
              className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]"
            />
            Obligatorio
          </label>
          <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
            <input
              type="checkbox"
              checked={form.is_eliminator ?? false}
              onChange={(e) => setForm({ ...form, is_eliminator: e.target.checked })}
              className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]"
            />
            Eliminatorio
          </label>
          <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
            <input
              type="checkbox"
              checked={form.evidence_required ?? false}
              onChange={(e) => setForm({ ...form, evidence_required: e.target.checked })}
              className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]"
            />
            Evidencia requerida
          </label>
        </div>
      </div>
    </Modal>
  )
}