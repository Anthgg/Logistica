import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import { supplierEvaluationTemplatesApi } from '../api/supplierEvaluationTemplatesApi'
import type {
  ConflictOfInterestDeclarationInput,
  EvaluationExchangeRateInput,
  QuotationEvaluation,
  QuotationRoundSummary,
  SupplierEvaluationTemplate,
  SupplierEvaluationTemplateVersion,
} from '../types/evaluation'
import { roundStatusLabel, generateIdempotencyKey } from '../format'
import { ErrorState, StatusPill } from './ui/SharedState'
import { DecimalInput } from './ui/DecimalInput'

const STEPS = [
  'Seleccionar ronda',
  'Validar estado',
  'Seleccionar plantilla',
  'Revisar versión',
  'Revisar candidatos',
  'Política de moneda',
  'Registrar tasas',
  'Revisar criterios',
  'Declarar conflictos',
  'Crear evaluación',
] as const

export function CreateQuotationEvaluationWizard() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [rounds, setRounds] = useState<QuotationRoundSummary[]>([])
  const [roundId, setRoundId] = useState<string | null>(null)
  const [round, setRound] = useState<QuotationRoundSummary | null>(null)
  const [templates, setTemplates] = useState<SupplierEvaluationTemplate[]>([])
  const [templateId, setTemplateId] = useState<string | null>(null)
  const [versions, setVersions] = useState<SupplierEvaluationTemplateVersion[]>([])
  const [versionId, setVersionId] = useState<string | null>(null)
  const [comparisonCurrency, setComparisonCurrency] = useState<string>('')
  const [rates, setRates] = useState<EvaluationExchangeRateInput[]>([])
  const [conflicts, setConflicts] = useState<ConflictOfInterestDeclarationInput[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    quotationEvaluationsApi
      .listEvaluableRounds({ page: 1, page_size: 50 })
      .then((res) => setRounds(res.items ?? []))
      .catch(() => setRounds([]))
      .finally(() => setLoading(false))
    supplierEvaluationTemplatesApi
      .list({ page: 1, page_size: 100 })
      .then((res) => setTemplates(res.items ?? []))
      .catch(() => setTemplates([]))
  }, [])

  const selectedTemplate = useMemo(
    () => templates.find((t) => t.id === templateId) ?? null,
    [templates, templateId],
  )
  const selectedVersion = useMemo(
    () => versions.find((v) => v.id === versionId) ?? null,
    [versions, versionId],
  )

  const loadVersions = async (tId: string) => {
    try {
      const vs = await supplierEvaluationTemplatesApi.listVersions(tId)
      setVersions(vs)
      const active = vs.find((v) => v.status === 'ACTIVE') ?? null
      setVersionId(active?.id ?? null)
    } catch {
      setVersions([])
    }
  }

  useEffect(() => {
    if (!roundId) {
      setRound(null)
      return
    }
    quotationEvaluationsApi
      .getRound(roundId)
      .then(setRound)
      .catch(() => setRound(null))
  }, [roundId])

  const handleCreate = async () => {
    if (!roundId || !versionId) {
      setError('Faltan datos para crear la evaluación.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      // Declarar conflictos primero (no bloquea creación)
      const created: QuotationEvaluation = await quotationEvaluationsApi.createFromRound(
        {
          round_id: roundId,
          template_version_id: versionId,
          comparison_currency: comparisonCurrency || null,
          exchange_rates: rates,
        },
        generateIdempotencyKey(),
      )
      // Declarar conflictos en la evaluación recién creada
      for (const c of conflicts) {
        try {
          await quotationEvaluationsApi.declareConflict(created.id, c)
        } catch {
          // no aborta
        }
      }
      navigate(`/logistics/purchasing/evaluations/${created.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo crear la evaluación.')
    } finally {
      setSubmitting(false)
    }
  }

  const canNext = useMemo(() => {
    switch (step) {
      case 0: return !!roundId
      case 2: return !!templateId
      case 3: return !!versionId
      case 6: return rates.every((r) => r.source.trim() && r.rate_date.trim())
      case 8: return true
      case 9: return false
      default: return true
    }
  }, [step, roundId, templateId, versionId, rates])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">Nueva evaluación</h1>
        <button
          type="button"
          onClick={() => navigate('/logistics/purchasing/evaluations')}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          Cancelar
        </button>
      </div>

      {/* Stepper */}
      <ol className="flex flex-wrap gap-2 text-xs">
        {STEPS.map((label, i) => (
          <li key={label}>
            <button
              type="button"
              onClick={() => setStep(i)}
              className={
                step === i
                  ? 'rounded-full bg-[#1F4E6D] px-3 py-1 font-semibold text-white'
                  : i < step
                    ? 'rounded-full bg-emerald-50 px-3 py-1 font-semibold text-emerald-700'
                    : 'rounded-full bg-slate-100 px-3 py-1 text-slate-500 hover:bg-slate-200'
              }
            >
              {i + 1}. {label}
            </button>
          </li>
        ))}
      </ol>

      {error && <ErrorState message={error} />}

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        {/* Paso 0: ronda */}
        {step === 0 && (
          <div className="space-y-3">
            <h2 className="text-sm font-bold">Selecciona una ronda cerrada</h2>
            {loading ? (
              <p className="text-xs text-slate-500">Cargando rondas evaluables…</p>
            ) : rounds.length === 0 ? (
              <p className="text-xs text-slate-500">
                No hay rondas evaluables. Solo se muestran rondas cerradas, en
                revisión interna o con respuestas abiertas y candidatos válidos.
              </p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="min-w-full divide-y divide-slate-100 text-xs">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-2 py-1.5 text-left">REQ</th>
                      <th className="px-2 py-1.5 text-left">Ronda</th>
                      <th className="px-2 py-1.5 text-left">Estado</th>
                      <th className="px-2 py-1.5 text-left">Deadline</th>
                      <th className="px-2 py-1.5 text-right">Proveedores</th>
                      <th className="px-2 py-1.5 text-right">Respuestas válidas</th>
                      <th className="px-2 py-1.5 text-left">Monedas</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {rounds.map((r) => (
                      <tr
                        key={r.id}
                        className={roundId === r.id ? 'bg-indigo-50/60' : 'hover:bg-slate-50/60'}
                      >
                        <td className="px-2 py-1.5 font-mono">{r.requisition_code}</td>
                        <td className="px-2 py-1.5">#{r.round_number}</td>
                        <td className="px-2 py-1.5"><StatusPill tone="info">{roundStatusLabel(r.status)}</StatusPill></td>
                        <td className="px-2 py-1.5">{r.deadline ? new Date(r.deadline).toLocaleDateString('es-PE') : '—'}</td>
                        <td className="px-2 py-1.5 text-right font-mono">{r.suppliers_count}</td>
                        <td className="px-2 py-1.5 text-right font-mono">{r.valid_responses_count}</td>
                        <td className="px-2 py-1.5">{r.currencies.join(', ') || '—'}</td>
                        <td className="px-2 py-1.5 text-right">
                          <button
                            type="button"
                            onClick={() => setRoundId(r.id)}
                            className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold"
                          >
                            {roundId === r.id ? 'Seleccionada' : 'Elegir'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Paso 1: validar estado */}
        {step === 1 && round && (
          <div className="space-y-2 text-xs">
            <h2 className="text-sm font-bold">Estado de la ronda</h2>
            <p>Ronda #{round.round_number} · {roundStatusLabel(round.status)}</p>
            <p>Respuestas válidas: {round.valid_responses_count}</p>
            <p>Respuestas selladas: {round.is_sealed ? 'Sí' : 'No'}</p>
            <p>Candidatos válidos: {round.has_open_responses ? 'Con respuestas abiertas' : 'Revisar'}</p>
            {!round.valid_responses_count && (
              <p className="text-rose-600">La ronda no tiene respuestas válidas.</p>
            )}
          </div>
        )}

        {/* Paso 2: plantilla */}
        {step === 2 && (
          <div className="space-y-3">
            <h2 className="text-sm font-bold">Selecciona plantilla</h2>
            <Select value={templateId ?? ''} onValueChange={(v) => { setTemplateId(v); void loadVersions(v) }}>
              <SelectTrigger><SelectValue placeholder="Plantilla" /></SelectTrigger>
              <SelectContent>
                {templates.map((t) => (
                  <SelectItem key={t.id} value={t.id}>{t.code} — {t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedTemplate && (
              <p className="text-xs text-slate-500">
                Scope: {selectedTemplate.scope} · Criterios: {selectedTemplate.criteria_count}
              </p>
            )}
          </div>
        )}

        {/* Paso 3: versión */}
        {step === 3 && (
          <div className="space-y-3">
            <h2 className="text-sm font-bold">Revisa la versión</h2>
            <Select value={versionId ?? ''} onValueChange={setVersionId}>
              <SelectTrigger><SelectValue placeholder="Versión" /></SelectTrigger>
              <SelectContent>
                {versions.map((v) => (
                  <SelectItem key={v.id} value={v.id}>{v.version} — {v.status}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedVersion && (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <span>Escala: {selectedVersion.scale}</span>
                <span>Empate: {selectedVersion.tie_policy}</span>
                <span>Adjudicación: {selectedVersion.award_policy}</span>
                <span>Motor: {selectedVersion.engine}</span>
                <span>Moneda: {selectedVersion.comparison_currency ?? '—'}</span>
                <span>Criterios: {selectedVersion.criteria.length}</span>
              </div>
            )}
            {versions.filter((v) => v.status === 'ACTIVE').length === 0 && (
              <p className="text-xs text-amber-600">La plantilla no tiene versión activa.</p>
            )}
          </div>
        )}

        {/* Paso 4: candidatos */}
        {step === 4 && (
          <div className="space-y-2">
            <h2 className="text-sm font-bold">Revisa candidatos (vista resumida)</h2>
            <p className="text-xs text-slate-500">
              Los candidatos se cargan tras crear la evaluación. Aquí se muestra
              un resumen preliminar de la ronda.
            </p>
            <p className="text-xs">Proveedores: {round?.suppliers_count ?? '—'} · Respuestas válidas: {round?.valid_responses_count ?? '—'}</p>
          </div>
        )}

        {/* Paso 5: moneda */}
        {step === 5 && (
          <div className="space-y-3">
            <h2 className="text-sm font-bold">Política de moneda de comparación</h2>
            <p className="text-xs text-slate-500">
              No se consulta tipo de cambio desde React. La conversión la realiza
              el backend con tasas registradas, fuente y fecha.
            </p>
            <DecimalInput
              label="Moneda de comparación (código ISO)"
              value={comparisonCurrency}
              onChange={setComparisonCurrency}
              placeholder="PEN"
              maxDecimals={0}
            />
            {round && (
              <p className="text-xs">Monedas en respuestas: {round.currencies.join(', ') || '—'}</p>
            )}
          </div>
        )}

        {/* Paso 6: tasas */}
        {step === 6 && (
          <div className="space-y-3">
            <h2 className="text-sm font-bold">Registrar tasas (cuando corresponda)</h2>
            <p className="text-xs text-slate-500">
              Cada tasa debe tener fuente y fecha. Sin fuente y fecha no se acepta.
            </p>
            <RateEditor
              currencies={round?.currencies ?? []}
              comparisonCurrency={comparisonCurrency}
              rates={rates}
              onChange={setRates}
            />
          </div>
        )}

        {/* Paso 7: criterios */}
        {step === 7 && selectedVersion && (
          <div className="space-y-2">
            <h2 className="text-sm font-bold">Revisa criterios</h2>
            <div className="overflow-x-auto rounded-lg border border-slate-200">
              <table className="min-w-full divide-y divide-slate-100 text-xs">
                <thead className="bg-slate-50 text-slate-500">
                  <tr>
                    <th className="px-2 py-1.5 text-left">Código</th>
                    <th className="px-2 py-1.5 text-left">Nombre</th>
                    <th className="px-2 py-1.5 text-left">Grupo</th>
                    <th className="px-2 py-1.5 text-right">Peso</th>
                    <th className="px-2 py-1.5 text-center">Elimin.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {selectedVersion.criteria.map((c) => (
                    <tr key={c.id}>
                      <td className="px-2 py-1.5 font-mono">{c.code}</td>
                      <td className="px-2 py-1.5">{c.name}</td>
                      <td className="px-2 py-1.5">{c.group}</td>
                      <td className="px-2 py-1.5 text-right font-mono">{c.weight}</td>
                      <td className="px-2 py-1.5 text-center">{c.is_eliminator ? 'Sí' : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Paso 8: conflictos */}
        {step === 8 && (
          <div className="space-y-3">
            <h2 className="text-sm font-bold">Declaración de conflicto de interés</h2>
            <p className="text-xs text-slate-500">
              El backend puede bloquear a un usuario para puntuar si hay conflicto
              confirmado. Declara por proveedor.
            </p>
            <ConflictDeclaration
              conflicts={conflicts}
              setConflicts={setConflicts}
            />
          </div>
        )}

        {/* Paso 9: crear */}
        {step === 9 && (
          <div className="space-y-3 text-xs">
            <h2 className="text-sm font-bold">Crear evaluación</h2>
            <ul className="space-y-1">
              <li>Ronda: #{round?.round_number ?? '—'}</li>
              <li>Plantilla: {selectedTemplate?.code ?? '—'}</li>
              <li>Versión: {selectedVersion?.version ?? '—'}</li>
              <li>Moneda: {comparisonCurrency || '—'}</li>
              <li>Tasas: {rates.length}</li>
              <li>Conflictos declarados: {conflicts.length}</li>
            </ul>
            <p className="rounded-lg border border-slate-200 bg-slate-50 p-2">
              Al crear la evaluación no se emite orden de compra ni se aprueba gasto.
            </p>
          </div>
        )}

        {/* Navegación */}
        <div className="mt-4 flex items-center justify-between">
          <button
            type="button"
            disabled={step === 0}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
          >
            Anterior
          </button>
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              disabled={!canNext}
              onClick={() => setStep((s) => s + 1)}
              className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-40"
            >
              Siguiente
            </button>
          ) : (
            <button
              type="button"
              disabled={submitting}
              onClick={handleCreate}
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {submitting ? 'Creando…' : 'Crear evaluación'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function RateEditor({
  currencies,
  comparisonCurrency,
  rates,
  onChange,
}: {
  currencies: string[]
  comparisonCurrency: string
  rates: EvaluationExchangeRateInput[]
  onChange: (r: EvaluationExchangeRateInput[]) => void
}) {
  return (
    <div className="space-y-2">
      {currencies.filter((c) => c !== comparisonCurrency).length === 0 && (
        <p className="text-xs text-slate-500">No se requieren tasas (moneda única).</p>
      )}
      {currencies
        .filter((c) => c !== comparisonCurrency)
        .map((cur) => {
          const existing = rates.find((r) => r.from_currency === cur) ?? {
            from_currency: cur,
            to_currency: comparisonCurrency,
            rate: '',
            source: '',
            rate_date: '',
          }
          return (
            <div key={cur} className="grid grid-cols-2 gap-2 rounded-lg border border-slate-200 p-2 text-xs md:grid-cols-4">
              <div>
                <div className="font-bold">{cur} → {comparisonCurrency}</div>
                <DecimalInput
                  value={existing.rate}
                  onChange={(v) => {
                    const has = rates.some((r) => r.from_currency === cur)
                    onChange(has
                      ? rates.map((r) => (r.from_currency === cur ? { ...r, rate: v } : r))
                      : [...rates, { ...existing, rate: v }])
                  }}
                  maxDecimals={6}
                />
              </div>
              <div>
                <label className="text-xs font-bold">Fuente</label>
                <input
                  value={existing.source}
                  onChange={(e) => {
                    const next = rates.some((r) => r.from_currency === cur)
                      ? rates.map((r) => r.from_currency === cur ? { ...r, source: e.target.value } : r)
                      : [...rates, { ...existing, source: e.target.value }]
                    onChange(next)
                  }}
                  className="w-full rounded-lg border border-slate-300 px-2 py-1 text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-bold">Fecha</label>
                <input
                  type="date"
                  value={existing.rate_date}
                  onChange={(e) => {
                    const next = rates.some((r) => r.from_currency === cur)
                      ? rates.map((r) => r.from_currency === cur ? { ...r, rate_date: e.target.value } : r)
                      : [...rates, { ...existing, rate_date: e.target.value }]
                    onChange(next)
                  }}
                  className="w-full rounded-lg border border-slate-300 px-2 py-1 text-xs"
                />
              </div>
            </div>
          )
        })}
    </div>
  )
}

function ConflictDeclaration({
  conflicts,
  setConflicts,
}: {
  conflicts: ConflictOfInterestDeclarationInput[]
  setConflicts: (c: ConflictOfInterestDeclarationInput[]) => void
}) {
  // Sin lista de proveedores aquí (se declaran por ID). Input libre de supplier_id.
  const [supplierId, setSupplierId] = useState('')
  const [status, setStatus] = useState<ConflictOfInterestDeclarationInput['status']>('NONE')
  const [explanation, setExplanation] = useState('')

  const add = () => {
    if (!supplierId.trim()) return
    setConflicts([
      ...conflicts,
      { supplier_id: supplierId.trim(), status, explanation: explanation.trim() || null },
    ])
    setSupplierId('')
    setExplanation('')
    setStatus('NONE')
  }

  return (
    <div className="space-y-2">
      <div className="rounded-lg border border-slate-200 p-2">
        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          <input
            placeholder="ID proveedor"
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
            className="rounded-lg border border-slate-300 px-2 py-1 text-xs font-mono"
          />
          <Select value={status} onValueChange={(v) => setStatus(v as ConflictOfInterestDeclarationInput['status'])}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="NONE">Sin conflicto</SelectItem>
              <SelectItem value="POSSIBLE">Posible conflicto</SelectItem>
              <SelectItem value="CONFIRMED">Conflicto confirmado</SelectItem>
              <SelectItem value="CANNOT_DECLARE">No puedo declarar</SelectItem>
            </SelectContent>
          </Select>
          <button
            type="button"
            onClick={add}
            className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold hover:bg-slate-50"
          >
            Agregar
          </button>
        </div>
        <textarea
          placeholder="Explicación (opcional)"
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          rows={2}
          className="mt-2 w-full rounded-lg border border-slate-300 px-2 py-1 text-xs"
        />
      </div>
      {conflicts.length > 0 && (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 text-xs">
          {conflicts.map((c) => (
            <li key={c.supplier_id} className="flex items-center justify-between px-2 py-1.5">
              <span><span className="font-mono">{c.supplier_id}</span> — {c.status}</span>
              <button
                type="button"
                onClick={() => setConflicts(conflicts.filter((x) => x.supplier_id !== c.supplier_id))}
                className="text-rose-600 hover:underline"
              >
                Quitar
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}