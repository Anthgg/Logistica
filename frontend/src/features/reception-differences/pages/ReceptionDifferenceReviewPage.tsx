import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceCasesApi } from '../api/receptionDifferenceCasesApi'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { ReceptionDifferenceEvidencePanel } from '../components/ReceptionDifferenceEvidencePanel'
import { ResponsiblePartyProposalPanel } from '../components/ResponsiblePartyProposalPanel'
import type { ReceptionDifferenceCaseDetail } from '../types/reception-differences'

export default function ReceptionDifferenceReviewPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const auth = useLogisticsPermissions()
  const [decision, setDecision] = useState<'APPROVE' | 'REQUEST_CHANGES'>('APPROVE')
  const [comment, setComment] = useState('')
  const [changesDescription, setChangesDescription] = useState('')

  const { data: caseData, isLoading: loading } = useQuery<ReceptionDifferenceCaseDetail>(
    ['reception-difference-case', caseId],
    `/logistics/reception-difference-cases/${caseId}`,
    undefined,
    { enabled: !!caseId },
  )

  const approveMutation = useMutation(
    (id: string) =>
      receptionDifferenceCasesApi.approve(id, {
        decision: 'APPROVE',
        comments: comment || undefined,
      }),
    { onSuccess: () => navigate(-1) }
  )

  const requestChangesMutation = useMutation(
    (id: string) =>
      receptionDifferenceCasesApi.requestChanges(id, {
        reason: changesDescription,
      }),
    { onSuccess: () => navigate(-1) }
  )

  const handleSubmit = () => {
    if (decision === 'APPROVE') {
      approveMutation.mutate(caseId!)
    } else {
      if (!changesDescription.trim()) return
      requestChangesMutation.mutate(caseId!)
    }
  }

  const canReview = auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.review || LOGISTICS_PERMISSIONS.receptionDifferences.approve)

  if (loading || !caseData) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-slate-500">
        {loading ? 'Cargando caso...' : 'Caso no encontrado'}
      </div>
    )
  }

  if (!canReview) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-red-500">
        Sin permisos de revisión
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-bold text-slate-800">Revisión — {caseData.case_code ?? caseData.case_id}</h1>
            <p className="text-xs text-slate-500">Decidir: aprobar, solicitar cambios o rechazar</p>
          </div>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600"
          >
            Volver
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-4xl space-y-6 p-6">
        {/* Summary */}
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-bold text-slate-800">Resumen del caso</h2>
          <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
            <InfoCell label="Recepción" value={caseData.receiving_code ?? caseData.receipt_code ?? '—'} />
            <InfoCell label="Proveedor" value={caseData.supplier?.name ?? caseData.supplier_name ?? '—'} />
            <InfoCell label="Transportista" value={caseData.carrier?.name ?? caseData.carrier_name ?? '—'} />
            <InfoCell label="Creado por" value={caseData.created_by?.display_name ?? '—'} />
          </div>
          {caseData.summary && (
            <p className="mt-3 text-xs text-slate-600">{caseData.summary}</p>
          )}
        </section>

        {/* Evidence */}
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <ReceptionDifferenceEvidencePanel evidence={Array.isArray(caseData.evidence) ? caseData.evidence : []} />
        </section>

        {/* Responsibility */}
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <ResponsiblePartyProposalPanel parties={Array.isArray(caseData.responsibility) ? [] : (caseData.responsibility?.proposed_parties ?? [])} />
        </section>

        {/* Decision */}
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-bold text-slate-800">Decisión de revisión</h2>

          <div className="mb-4 flex gap-2">
            <button
              type="button"
              onClick={() => setDecision('APPROVE')}
              className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                decision === 'APPROVE'
                  ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                  : 'border-slate-200 text-slate-600'
              }`}
            >
              Aprobar
            </button>
            <button
              type="button"
              onClick={() => setDecision('REQUEST_CHANGES')}
              className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                decision === 'REQUEST_CHANGES'
                  ? 'border-amber-300 bg-amber-50 text-amber-700'
                  : 'border-slate-200 text-slate-600'
              }`}
            >
              Solicitar cambios
            </button>
          </div>

          {decision === 'REQUEST_CHANGES' && (
            <label className="mb-3 block text-xs text-slate-600">
              Cambios solicitados *
              <textarea
                value={changesDescription}
                onChange={(e) => setChangesDescription(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
                rows={3}
                placeholder="Describa los cambios necesarios..."
              />
            </label>
          )}

          <label className="mb-4 block text-xs text-slate-600">
            Comentario (opcional)
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
              rows={2}
            />
          </label>

          {(approveMutation.error || requestChangesMutation.error) && (
            <p className="mb-3 text-xs text-rose-500">
              {String(approveMutation.error || requestChangesMutation.error)}
            </p>
          )}

          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={(approveMutation.isPending || requestChangesMutation.isPending) || (decision === 'REQUEST_CHANGES' && !changesDescription.trim())}
              className="rounded-lg bg-[#1F4E6D] px-4 py-2 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
            >
              {(approveMutation.isPending || requestChangesMutation.isPending) ? 'Procesando...' : decision === 'APPROVE' ? 'Aprobar caso' : 'Solicitar cambios'}
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase text-slate-400">{label}</p>
      <p className="text-slate-800">{value}</p>
    </div>
  )
}
