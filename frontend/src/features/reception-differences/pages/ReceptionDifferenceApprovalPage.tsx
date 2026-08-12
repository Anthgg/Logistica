import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceCasesApi } from '../api/receptionDifferenceCasesApi'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { ReceptionDifferenceAcknowledgementPanel } from '../components/ReceptionDifferenceAcknowledgementPanel'
import type { ReceptionDifferenceCaseDetail, ReceptionDifferenceResponsibleParty } from '../types/reception-differences'

export default function ReceptionDifferenceApprovalPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const auth = useLogisticsPermissions()
  const [decision, setDecision] = useState<'APPROVE' | 'REJECT'>('APPROVE')
  const [comment, setComment] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')

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

  const rejectMutation = useMutation(
    (id: string) =>
      receptionDifferenceCasesApi.requestChanges(id, { reason: rejectionReason }),
    { onSuccess: () => navigate(-1) }
  )

  const canApprove = auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.approve)

  if (loading || !caseData) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-slate-500">
        {loading ? 'Cargando caso...' : 'Caso no encontrado'}
      </div>
    )
  }

  if (!canApprove) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-red-500">
        Sin permisos de aprobación
      </div>
    )
  }

  const proposedParties: ReceptionDifferenceResponsibleParty[] = Array.isArray(caseData.responsibility)
    ? []
    : (caseData.responsibility?.proposed_parties ?? [])

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-bold text-slate-800">Aprobación — {caseData.case_code ?? caseData.case_id}</h1>
            <p className="text-xs text-slate-500">Verificar evidencia, responsabilidad y firmas antes de aprobar</p>
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
            <InfoCell label="Estado" value={caseData.current_status_display ?? caseData.status} />
          </div>
          {caseData.summary && (
            <p className="mt-3 text-xs text-slate-600">{caseData.summary}</p>
          )}
        </section>

        {/* Responsibility */}
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <ResponsiblePartyProposalPanel parties={proposedParties} />
        </section>

        {/* Acknowledgements */}
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <ReceptionDifferenceAcknowledgementPanel acknowledgements={caseData.reviews?.acknowledgements ?? []} />
        </section>

        {/* Approval Decision */}
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-bold text-slate-800">Decisión de aprobación</h2>

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
              onClick={() => setDecision('REJECT')}
              className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                decision === 'REJECT'
                  ? 'border-rose-300 bg-rose-50 text-rose-700'
                  : 'border-slate-200 text-slate-600'
              }`}
            >
              Rechazar
            </button>
          </div>

          {decision === 'REJECT' && (
            <label className="mb-3 block text-xs text-slate-600">
              Motivo del rechazo *
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
                rows={3}
                placeholder="Describa el motivo del rechazo..."
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

          {(approveMutation.error || rejectMutation.error) && (
            <p className="mb-3 text-xs text-rose-500">
              {String(approveMutation.error || rejectMutation.error)}
            </p>
          )}

          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => {
                if (decision === 'APPROVE') {
                  approveMutation.mutate(caseId!)
                } else {
                  if (!rejectionReason.trim()) return
                  rejectMutation.mutate(caseId!)
                }
              }}
              disabled={(approveMutation.isPending || rejectMutation.isPending) || (decision === 'REJECT' && !rejectionReason.trim())}
              className="rounded-lg bg-[#1F4E6D] px-4 py-2 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
            >
              {(approveMutation.isPending || rejectMutation.isPending)
                ? 'Procesando...'
                : decision === 'APPROVE'
                  ? 'Aprobar y generar documento DIF'
                  : 'Rechazar caso'}
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

function ResponsiblePartyProposalPanel({ parties }: { parties: import('../types/reception-differences').ReceptionDifferenceResponsibleParty[] }) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-slate-800">Responsables</h3>
      {parties.length === 0 ? (
        <p className="text-xs text-slate-400">No hay responsables asignados.</p>
      ) : (
        <div className="space-y-2">
          {parties.map((p) => (
            <div key={p.responsibility_id} className="rounded-lg border border-slate-200 p-3 text-xs">
              <span className="font-semibold text-slate-800">{p.party_name}</span>
              <span className="ml-2 text-slate-500">{p.role} · {p.percentage ?? '—'}%</span>
              {p.rationale && <p className="mt-1 text-slate-600">{p.rationale}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
