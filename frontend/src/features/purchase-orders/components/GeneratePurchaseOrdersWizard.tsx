import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { purchaseOrdersV2Api } from '../api/purchaseOrdersV2Api'
import { EmptyState, ErrorState, StatusPill } from './ui'
import { formatDecimal, formatMoney } from '../format'
import type { PurchaseOrderGenerationPlan } from '../types/phase034-contract'

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export function GeneratePurchaseOrdersWizard() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const permissions = useLogisticsPermissions()
  const canGenerate = permissions.hasPermission(
    LOGISTICS_PERMISSIONS.purchaseOrdersV2.generate,
  )
  const [decisionId, setDecisionId] = useState(
    searchParams.get('decisionId') ?? '',
  )
  const [plan, setPlan] = useState<PurchaseOrderGenerationPlan | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const normalizedDecisionId = decisionId.trim()
  const isValidDecisionId = UUID_PATTERN.test(normalizedDecisionId)
  const entries = plan?.entries ?? []
  const blockingIssues = plan?.blocking_issues ?? []
  const warnings = plan?.warnings ?? []

  const planLineCount = entries.reduce(
    (total, entry) => total + (entry.lines?.length ?? 0),
    0,
  )

  const createPlan = async () => {
    if (!canGenerate || !isValidDecisionId) return
    setIsLoading(true)
    setErrorMessage(null)
    setPlan(null)
    try {
      const response = await purchaseOrdersV2Api.createGenerationPlan({
        evaluation_decision_id: normalizedDecisionId,
      })
      setPlan(response)
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudo crear la previsualización.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  if (!canGenerate) {
    return (
      <ErrorState message="No tienes la capability de generación de órdenes de compra." />
    )
  }

  return (
    <section className="space-y-5" aria-labelledby="generation-title">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#1F4E6D]">
            Fase 034 · Paso seguro
          </p>
          <h1
            id="generation-title"
            className="mt-1 text-xl font-bold text-slate-950"
          >
            Previsualizar órdenes desde una decisión
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">
            El backend valida que la decisión exista y sea ejecutable. Esta
            pantalla no crea órdenes porque el contrato 0.9.1 solo publica la
            planificación.
          </p>
        </div>
        <button
          type="button"
          onClick={() =>
            navigate('/logistics/purchasing/purchase-orders')
          }
          className="min-h-11 rounded-lg border border-slate-200 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Volver al listado
        </button>
      </header>

      <ol
        aria-label="Progreso de generación"
        className="grid gap-2 text-sm sm:grid-cols-3"
      >
        {[
          ['1', 'Identificar decisión'],
          ['2', 'Consultar plan real'],
          ['3', 'Revisar bloqueos'],
        ].map(([number, label], index) => {
          const active = index === 0 ? !plan : index === 1 ? isLoading : !!plan
          return (
            <li
              key={number}
              className={
                active
                  ? 'rounded-xl border border-[#1F4E6D]/30 bg-[#1F4E6D]/5 p-3 text-[#1F4E6D]'
                  : 'rounded-xl border border-slate-200 bg-white p-3 text-slate-500'
              }
            >
              <span className="font-bold">{number}.</span> {label}
            </li>
          )
        })}
      </ol>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <label className="block">
          <span className="text-sm font-semibold text-slate-800">
            ID de la decisión de evaluación
          </span>
          <span className="mt-1 block text-xs text-slate-500">
            Se completa automáticamente al llegar desde la decisión. Mientras
            esa ruta no esté publicada, puede introducirse el UUID para
            consultar el plan validado por el servidor.
          </span>
          <div className="mt-3 flex flex-col gap-2 sm:flex-row">
            <input
              value={decisionId}
              onChange={(event) => setDecisionId(event.target.value)}
              autoComplete="off"
              spellCheck={false}
              aria-invalid={decisionId.length > 0 && !isValidDecisionId}
              placeholder="00000000-0000-0000-0000-000000000000"
              className="min-h-11 min-w-0 flex-1 rounded-lg border border-slate-300 px-3 font-mono text-sm outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
            />
            <button
              type="button"
              disabled={!isValidDecisionId || isLoading}
              onClick={() => void createPlan()}
              className="min-h-11 rounded-lg bg-[#1F4E6D] px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? 'Consultando…' : 'Crear plan'}
            </button>
          </div>
          {decisionId.length > 0 && !isValidDecisionId && (
            <span className="mt-2 block text-xs font-medium text-rose-600">
              Introduce un UUID válido.
            </span>
          )}
        </label>
      </div>

      {errorMessage && <ErrorState message={errorMessage} />}

      {!plan && !errorMessage && !isLoading && (
        <EmptyState
          title="Aún no hay un plan"
          description="Consulta una decisión para ver la agrupación real por proveedor y moneda."
        />
      )}

      {plan && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-4">
            <StatusPill tone={plan.is_executable ? 'success' : 'danger'}>
              {plan.is_executable ? 'Plan ejecutable' : 'Plan bloqueado'}
            </StatusPill>
            <span className="text-sm text-slate-600">
              Estado de decisión: <strong>{plan.evaluation_decision_status}</strong>
            </span>
            <span className="text-sm text-slate-600">
              Órdenes previstas:{' '}
              <strong>{plan.total_orders_to_create}</strong>
            </span>
            <span className="text-sm text-slate-600">
              Líneas: <strong>{planLineCount}</strong>
            </span>
          </div>

          {blockingIssues.length > 0 && (
            <div
              role="alert"
              className="rounded-xl border border-rose-200 bg-rose-50 p-4"
            >
              <h2 className="text-sm font-bold text-rose-800">
                Bloqueos del backend
              </h2>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-rose-700">
                {blockingIssues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            </div>
          )}

          {warnings.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <h2 className="text-sm font-bold text-amber-800">
                Advertencias
              </h2>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-700">
                {warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid gap-3 lg:grid-cols-2">
            {entries.map((entry) => (
              <article
                key={`${entry.entry_index}-${entry.supplier_business_partner_id}-${entry.currency_code}`}
                className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
              >
                <header className="border-b border-slate-100 bg-slate-50/70 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="text-xs font-semibold text-[#1F4E6D]">
                        OC prevista {entry.entry_index + 1}
                      </p>
                      <h2 className="mt-1 text-base font-bold text-slate-900">
                        {entry.supplier_name_snapshot}
                      </h2>
                    </div>
                    <StatusPill>{entry.currency_code}</StatusPill>
                  </div>
                  <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <dt className="text-slate-500">Subtotal estimado</dt>
                      <dd className="font-mono font-semibold text-slate-800">
                        {formatMoney(
                          entry.estimated_subtotal,
                          entry.currency_code,
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-slate-500">Total estimado</dt>
                      <dd className="font-mono font-semibold text-slate-800">
                        {formatMoney(
                          entry.estimated_grand_total,
                          entry.currency_code,
                        )}
                      </dd>
                    </div>
                  </dl>
                </header>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-100 text-xs">
                    <thead className="text-left font-semibold text-slate-500">
                      <tr>
                        <th className="px-4 py-2">Producto</th>
                        <th className="px-4 py-2 text-right">Cantidad</th>
                        <th className="px-4 py-2 text-right">Precio</th>
                        <th className="px-4 py-2 text-right">Total fuente</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {(entry.lines ?? []).map((line) => (
                        <tr key={line.evaluation_decision_line_id}>
                          <td className="px-4 py-2">
                            {line.product_name_snapshot}
                          </td>
                          <td className="px-4 py-2 text-right font-mono">
                            {formatDecimal(line.ordered_quantity, 6)}{' '}
                            {line.ordered_unit_code}
                          </td>
                          <td className="px-4 py-2 text-right font-mono">
                            {formatMoney(line.unit_price, line.currency_code)}
                          </td>
                          <td className="px-4 py-2 text-right font-mono">
                            {formatMoney(
                              line.source_line_total,
                              line.currency_code,
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>
            ))}
          </div>

          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <strong>Ejecución no disponible:</strong> el OpenAPI 0.9.1 no
            publica un endpoint para ejecutar el plan. No se habilita un botón
            ficticio ni se crean órdenes localmente.
          </div>
        </div>
      )}
    </section>
  )
}
