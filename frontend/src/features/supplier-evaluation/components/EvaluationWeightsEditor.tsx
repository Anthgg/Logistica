import { useEffect, useMemo, useState } from 'react'
import { supplierEvaluationTemplatesApi } from '../api/supplierEvaluationTemplatesApi'
import type {
  EvaluationCriterionDefinition,
  EvaluationWeightsValidation,
  SupplierEvaluationTemplateVersion,
} from '../types/evaluation'
import { visualDiff, visualSum } from '../format'
import { DecimalInput } from './ui/DecimalInput'

type WeightState = Record<string, string>

export function EvaluationWeightsEditor({
  templateId,
  version,
  criteria,
  canManage,
}: {
  templateId: string
  version: SupplierEvaluationTemplateVersion
  criteria: EvaluationCriterionDefinition[]
  canManage: boolean
}) {
  const [weights, setWeights] = useState<WeightState>(() =>
    Object.fromEntries(criteria.map((c) => [c.id, c.weight])),
  )
  const [validation, setValidation] = useState<EvaluationWeightsValidation | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setWeights(Object.fromEntries(criteria.map((c) => [c.id, c.weight])))
  }, [criteria])

  const isLocked = version.status === 'ACTIVE' || version.status === 'ARCHIVED'
  const readOnly = isLocked || !canManage

  const visualTotal = useMemo(() => {
    const active = criteria.filter((c) => c.is_active)
    return visualSum(active.map((c) => weights[c.id] ?? c.weight))
  }, [criteria, weights])

  const visualDiffTo100 = visualDiff(visualTotal, '100')

  const localStatus: 'OK' | 'UNDER' | 'OVER' | 'INVALID' = (() => {
    const n = Number(visualTotal)
    if (!Number.isFinite(n)) return 'INVALID'
    if (n === 100) return 'OK'
    if (n < 100) return 'UNDER'
    return 'OVER'
  })()

  const handleValidate = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const res = await supplierEvaluationTemplatesApi.validateWeights(
        templateId,
        version.id,
        { weights },
      )
      setValidation(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo validar los pesos.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">
        Los pesos se manejan como texto decimal. La suma visual es una
        comprobación no autoritativa: el backend confirma si los pesos suman 100.
        {isLocked && ' La versión está bloqueada (estado: ' + version.status + ').'}
      </p>

      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50/60 text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2.5 text-left">Criterio</th>
              <th className="px-3 py-2.5 text-right">Peso</th>
              <th className="px-3 py-2.5 text-right">Total acumulado</th>
              <th className="px-3 py-2.5 text-right">Diferencia a 100</th>
              <th className="px-3 py-2.5 text-left">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {criteria.map((c) => {
              const acc = visualSum(
                criteria
                  .filter((x) => x.order <= c.order)
                  .map((x) => weights[x.id] ?? x.weight),
              )
              const diff = visualDiff(acc, '100')
              return (
                <tr key={c.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2 text-xs">
                    <span className="font-mono">{c.code}</span> · {c.name}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {readOnly ? (
                      <span className="font-mono text-xs">{weights[c.id] ?? c.weight}</span>
                    ) : (
                      <DecimalInput
                        value={weights[c.id] ?? c.weight}
                        onChange={(v) => setWeights((w) => ({ ...w, [c.id]: v }))}
                        maxDecimals={4}
                        className="w-28 ml-auto"
                        aria-label={`Peso de ${c.name}`}
                      />
                    )}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{acc}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{diff}</td>
                  <td className="px-3 py-2 text-xs">
                    {Number(acc) === 100 ? (
                      <span className="text-emerald-600">Correcto</span>
                    ) : Number(acc) < 100 ? (
                      <span className="text-amber-600">Falta peso</span>
                    ) : (
                      <span className="text-rose-600">Excede 100</span>
                    )}
                  </td>
                </tr>
              )
            })}
            <tr className="bg-slate-50/40 font-semibold">
              <td className="px-3 py-2 text-xs">Total</td>
              <td className="px-3 py-2 text-right font-mono text-xs">{visualTotal}</td>
              <td className="px-3 py-2" />
              <td className="px-3 py-2 text-right font-mono text-xs">{visualDiffTo100}</td>
              <td className="px-3 py-2 text-xs">
                {localStatus === 'OK' && <span className="text-emerald-600">Correcto</span>}
                {localStatus === 'UNDER' && <span className="text-amber-600">Falta peso</span>}
                {localStatus === 'OVER' && <span className="text-rose-600">Excede 100</span>}
                {localStatus === 'INVALID' && <span className="text-rose-600">Total inválido</span>}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {error && (
        <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      {validation && (
        <div
          className={`rounded-lg border px-3 py-2 text-xs ${
            validation.is_valid
              ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
              : 'border-rose-200 bg-rose-50 text-rose-700'
          }`}
        >
          <div className="font-semibold">
            {validation.is_valid ? 'Pesos válidos según backend' : 'Pesos inválidos según backend'}
          </div>
          <div className="mt-1 font-mono text-[11px]">
            Total: {validation.total} · Diferencia: {validation.difference}
          </div>
          {validation.issues.length > 0 && (
            <ul className="mt-1 list-disc pl-4">
              {validation.issues.map((iss) => (
                <li key={iss.code}>{iss.code}: {iss.message}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {!readOnly && (
        <div className="flex justify-end">
          <button
            type="button"
            disabled={submitting}
            onClick={handleValidate}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            {submitting ? 'Validando…' : 'Validar pesos con backend'}
          </button>
        </div>
      )}
    </div>
  )
}