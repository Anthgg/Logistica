import { useState } from 'react'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import type { EvaluationCapabilities, QuotationEvaluationRun } from '../types/evaluation'
import { generateIdempotencyKey } from '../format'
import { Modal } from './ui/Overlay'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

export function CalculateEvaluationDialog({
  evaluationId,
  capabilities,
  onChanged,
}: {
  evaluationId: string
  capabilities: EvaluationCapabilities
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [isRecalc, setIsRecalc] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [run, setRun] = useState<QuotationEvaluationRun | null>(null)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.supplierEvaluations.calculate,
  })

  const canCalc = capabilities.can_calculate
  const canRecalc = capabilities.can_recalculate

  const handleRun = async () => {
    setSubmitting(true)
    try {
      const executed = await guard.run(async () => {
        const key = generateIdempotencyKey()
        const r = isRecalc
          ? await quotationEvaluationsApi.recalculate(evaluationId, key)
          : await quotationEvaluationsApi.calculate(evaluationId, key)
        setRun(r)
      })
      if (executed) {
        setOpen(false)
        await onChanged()
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {canCalc && (
          <button
            type="button"
            disabled={guard.isBlocked}
            onClick={() => { setIsRecalc(false); setOpen(true) }}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            Calcular
          </button>
        )}
        {canRecalc && (
          <button
            type="button"
            disabled={guard.isBlocked}
            onClick={() => { setIsRecalc(true); setOpen(true) }}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Recalcular
          </button>
        )}
        {guard.isBlocked && (
          <span className="text-xs text-amber-600">Se requiere verificación reforzada para calcular.</span>
        )}
      </div>

      <Modal
        open={open}
        onOpenChange={setOpen}
        title={isRecalc ? 'Recalcular evaluación' : 'Calcular evaluación'}
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleRun} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Procesando…' : 'Confirmar'}</button>
          </>
        }
      >
        <div className="space-y-2 text-xs text-slate-600">
          <p>
            El cálculo se ejecuta en el backend. React no calcula puntajes ni
            ranking. Se enviará una idempotency key y se requiere step-up si la
            capability lo exige.
          </p>
          <ul className="list-disc pl-4">
            <li>Se valida el estado de la evaluación.</li>
            <li>Se obtiene CSRF.</li>
            <li>Se aplica idempotency key.</li>
            <li>Se consulta la corrida resultante.</li>
          </ul>
          {run && (
            <div className="rounded-lg border border-slate-200 p-2 font-mono">
              Corrida #{run.run_number} · {run.status} · motor {run.engine}
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}