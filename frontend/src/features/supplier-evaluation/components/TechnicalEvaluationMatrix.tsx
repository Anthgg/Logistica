import { useCallback, useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { evaluationScoresApi } from '../api/evaluationScoresApi'
import type {
  EvaluationCapabilities,
  QuotationEvaluationCandidate,
  TechnicalCompliance,
  TechnicalComplianceAssessment,
  TechnicalAssessmentInput,
} from '../types/evaluation'
import { complianceLabel } from '../format'
import { EmptyState, ErrorState, TableSkeleton } from './ui/SharedState'
import { Modal } from './ui/Overlay'

const COMPLIANCE_OPTIONS: TechnicalCompliance[] = [
  'COMPLIANT',
  'PARTIALLY_COMPLIANT',
  'NON_COMPLIANT',
  'ALTERNATIVE_REVIEW',
  'NOT_EVALUATED',
]

export function TechnicalEvaluationMatrix({
  evaluationId,
  candidates,
  capabilities,
}: {
  evaluationId: string
  candidates: QuotationEvaluationCandidate[]
  capabilities: EvaluationCapabilities
}) {
  const [rows, setRows] = useState<TechnicalComplianceAssessment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [filterCandidate, setFilterCandidate] = useState<string>('ALL')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<TechnicalAssessmentInput>({
    candidate_id: '',
    requirement_code: '',
    compliance: 'NOT_EVALUATED',
    deviation: null,
    evidence_id: null,
  })
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setRows(
        await evaluationScoresApi.listTechnicalAssessments(
          evaluationId,
          filterCandidate === 'ALL' ? undefined : filterCandidate,
        ),
      )
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudo cargar la evaluación técnica.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId, filterCandidate])

  useEffect(() => { void load() }, [load])

  const canCreate = capabilities.can_create_manual_score

  const handleSubmit = async () => {
    if (!form.candidate_id || !form.requirement_code.trim()) {
      alert('Candidato y requisito son obligatorios.')
      return
    }
    setSubmitting(true)
    try {
      await evaluationScoresApi.createTechnicalAssessment(evaluationId, form)
      setOpen(false)
      setForm({ candidate_id: '', requirement_code: '', compliance: 'NOT_EVALUATED', deviation: null, evidence_id: null })
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally {
      setSubmitting(false)
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Select value={filterCandidate} onValueChange={setFilterCandidate}>
          <SelectTrigger className="w-[260px]"><SelectValue placeholder="Proveedor" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Todos los proveedores</SelectItem>
            {candidates.map((c) => (
              <SelectItem key={c.id} value={c.id}>{c.supplier_name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {canCreate && (
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Registrar evaluación técnica
          </button>
        )}
      </div>

      {rows.length === 0 ? (
        <EmptyState title="Sin evaluaciones técnicas registradas" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Proveedor</th>
                <th className="px-3 py-2.5 text-left">Producto/línea</th>
                <th className="px-3 py-2.5 text-left">Requisito</th>
                <th className="px-3 py-2.5 text-left">Cumplimiento</th>
                <th className="px-3 py-2.5 text-left">Desviación</th>
                <th className="px-3 py-2.5 text-left">Evidencia</th>
                <th className="px-3 py-2.5 text-right">Puntaje</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2">{r.supplier_name}</td>
                  <td className="px-3 py-2">{r.product_name ?? r.line_id ?? '—'}</td>
                  <td className="px-3 py-2"><span className="font-mono">{r.requirement_code}</span> · {r.requirement_label}</td>
                  <td className="px-3 py-2">{complianceLabel(r.compliance)}</td>
                  <td className="px-3 py-2">{r.deviation ?? '—'}</td>
                  <td className="px-3 py-2">{r.evidence_name ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono">{r.score ?? '—'}</td>
                  <td className="px-3 py-2">{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Evaluación técnica"
        size="lg"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleSubmit} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Guardando…' : 'Guardar'}</button>
          </>
        }
      >
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Proveedor</label>
            <Select value={form.candidate_id} onValueChange={(v) => setForm({ ...form, candidate_id: v })}>
              <SelectTrigger><SelectValue placeholder="Selecciona proveedor" /></SelectTrigger>
              <SelectContent>
                {candidates.map((c) => <SelectItem key={c.id} value={c.id}>{c.supplier_name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Código de requisito</label>
              <input value={form.requirement_code} onChange={(e) => setForm({ ...form, requirement_code: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">ID línea (opcional)</label>
              <input value={form.line_id ?? ''} onChange={(e) => setForm({ ...form, line_id: e.target.value || null })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Cumplimiento</label>
            <Select value={form.compliance} onValueChange={(v) => setForm({ ...form, compliance: v as TechnicalCompliance })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {COMPLIANCE_OPTIONS.map((o) => <SelectItem key={o} value={o}>{complianceLabel(o)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Desviación</label>
            <textarea value={form.deviation ?? ''} onChange={(e) => setForm({ ...form, deviation: e.target.value || null })} rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <p className="text-[11px] text-slate-500">
            No se declara equivalencia de una alternativa automáticamente.
          </p>
        </div>
      </Modal>
    </div>
  )
}