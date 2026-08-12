import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { ReceptionDifferenceEvidencePanel } from '../components/ReceptionDifferenceEvidencePanel'
import { ReceptionDifferenceAcknowledgementPanel } from '../components/ReceptionDifferenceAcknowledgementPanel'
import { SubmitReceptionDifferenceCaseDialog } from '../components/SubmitReceptionDifferenceCaseDialog'
import { DisputeReceptionDifferenceDialog } from '../components/DisputeReceptionDifferenceDialog'
import { ShortageDifferencePanel } from '../components/difference-types/ShortageDifferencePanel'
import { OverageDifferencePanel } from '../components/difference-types/OverageDifferencePanel'
import { DamageDifferencePanel } from '../components/difference-types/DamageDifferencePanel'
import { WrongProductDifferencePanel } from '../components/difference-types/WrongProductDifferencePanel'
import { MissingDocumentDifferencePanel } from '../components/difference-types/MissingDocumentDifferencePanel'
import { BrokenSealDifferencePanel } from '../components/difference-types/BrokenSealDifferencePanel'
import { FutureQuarantineRecommendationsPanel, FutureClaimPreparationPanel, QualityInspectionPreparationPanel } from '../components/FuturePreparationPanels'
import type { ReceptionDifferenceCaseDetail, ReceptionDifferenceItem, ReceptionDifferenceCaseCapabilities, ReceptionDifferenceResponsibleParty } from '../types/reception-differences'

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Borrador',
  EVIDENCE_PENDING: 'Evidencia pendiente',
  RESPONSIBILITY_PENDING: 'Responsabilidad pendiente',
  IN_REVIEW: 'En revisión',
  CHANGES_REQUESTED: 'Cambios solicitados',
  PENDING_APPROVAL: 'Pendiente de aprobación',
  ISSUED: 'Emitido',
  ACKNOWLEDGED: 'Reconocido',
  DISPUTED: 'Disputado',
  FOLLOW_UP: 'Seguimiento',
  CLOSED: 'Cerrado',
  CANCELLED: 'Cancelado',
}

const SEVERITY_COLORS: Record<string, string> = {
  LOW: 'bg-slate-100 text-slate-700',
  MEDIUM: 'bg-amber-100 text-amber-700',
  HIGH: 'bg-orange-100 text-orange-700',
  CRITICAL: 'bg-rose-100 text-rose-700',
}

type DetailTab = 'summary' | 'items' | 'comparison' | 'evidence' | 'responsibilities' | 'reviews' | 'approvals' | 'acknowledgements' | 'document' | 'followup' | 'integrity' | 'history'

const TABS: { value: DetailTab; label: string }[] = [
  { value: 'summary', label: 'Resumen' },
  { value: 'items', label: 'Ítems' },
  { value: 'comparison', label: 'Comparación' },
  { value: 'evidence', label: 'Evidencias' },
  { value: 'responsibilities', label: 'Responsables' },
  { value: 'reviews', label: 'Revisiones' },
  { value: 'approvals', label: 'Aprobaciones' },
  { value: 'acknowledgements', label: 'Reconocimientos' },
  { value: 'document', label: 'Acta' },
  { value: 'followup', label: 'Seguimiento' },
  { value: 'integrity', label: 'Integridad' },
  { value: 'history', label: 'Historial' },
]

export function ReceptionDifferenceCaseDetailPage({ section: _section }: { section?: string }) {
  const { caseId } = useParams<{ caseId: string }>()
  const [activeTab, setActiveTab] = useState<DetailTab>('summary')
  const [showSubmitDialog, setShowSubmitDialog] = useState(false)
  const [disputeParty, setDisputeParty] = useState<ReceptionDifferenceResponsibleParty | null>(null)

  const caseQuery = useQuery<ReceptionDifferenceCaseDetail>(
    ['reception-difference-case', caseId],
    `/logistics/reception-difference-cases/${caseId}`,
    undefined,
    { enabled: !!caseId },
  )

  const capabilitiesQuery = useQuery<ReceptionDifferenceCaseCapabilities>(
    ['reception-difference-capabilities', caseId],
    `/logistics/reception-difference-cases/${caseId}/capabilities`,
    undefined,
    { enabled: !!caseId },
  )

  if (!caseId || !caseQuery.data) {
    return <div className="page"><div className="panel p-8 text-center text-sm text-slate-400">Cargando…</div></div>
  }

  const c = caseQuery.data
  const caps = capabilitiesQuery.data

  const proposedParties: ReceptionDifferenceResponsibleParty[] = Array.isArray(c.responsibility)
    ? []
    : (c.responsibility?.proposed_parties ?? [])

  const reviewsList = c.reviews?.reviews ?? []
  const approvalsList = c.reviews?.approvals ?? []
  const acksList = c.reviews?.acknowledgements ?? []

  const issuedDocs = Array.isArray(c.documents)
    ? c.documents.filter((d: any) => d.status === 'ISSUED')
    : (c.documents?.issued_documents ?? [])

  const pendingDocs = Array.isArray(c.documents)
    ? c.documents.filter((d: any) => d.status !== 'ISSUED')
    : (c.documents?.pending_documents ?? [])

  return (
    <div className="page">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-slate-800">{c.case_code ?? 'Sin código'}</h1>
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${SEVERITY_COLORS[c.severity]}`}>
              {c.severity}
            </span>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700">
              {STATUS_LABELS[c.status]}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Recepción: {c.receipt_code} · Proveedor: {c.supplier_name} · Almacén: {c.warehouse_name}
          </p>
        </div>
        <div className="flex gap-2">
          {caps?.can_submit && (
            <button
              type="button"
              onClick={() => setShowSubmitDialog(true)}
              className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55]"
            >
              Enviar a revisión
            </button>
          )}
        </div>
      </div>

      {c.warnings.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
          {c.warnings.map((w, i) => <p key={i}>{w}</p>)}
        </div>
      )}

      <div className="flex flex-wrap gap-1.5" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              activeTab === tab.value
                ? 'bg-[#1F4E6D] text-white'
                : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="panel p-4">
        {activeTab === 'summary' && (
          <div className="space-y-3 text-xs">
            <InfoRow label="Recepción" value={c.receipt_code} />
            <InfoRow label="Proveedor" value={c.supplier_name} />
            <InfoRow label="Almacén" value={c.warehouse_name} />
            <InfoRow label="Transportista" value={c.carrier_name ?? '—'} />
            <InfoRow label="OC" value={c.purchase_order_codes.join(', ') || '—'} />
            <InfoRow label="Ítems" value={String(c.items_count)} />
            <InfoRow label="Ítems críticos" value={String(c.critical_items_count)} />
            <InfoRow label="Evidencias" value={String(c.evidence_count)} />
            <InfoRow label="Responsable" value={c.primary_responsible?.party_name ?? '—'} />
            <InfoRow label="Responsabilidad" value={c.responsibility_status ?? '—'} />
            <InfoRow label="Disputas" value={c.has_disputes ? 'Sí' : 'No'} />
          </div>
        )}
        {activeTab === 'items' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Ítems ({c.items.length})</h3>
            {c.items.length === 0 ? (
              <p className="text-xs text-slate-400">No hay ítems registrados.</p>
            ) : (
              c.items.map((item) => <DifferenceItemCard key={item.item_id} item={item} />)
            )}
          </div>
        )}
        {activeTab === 'comparison' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Comparación por tipo</h3>
            {c.items.length === 0 ? (
              <p className="text-xs text-slate-400">No hay ítems para comparar.</p>
            ) : (
              c.items.map((item) => (
                <div key={item.item_id} className="rounded-lg border border-slate-200 p-3">
                  <ComparisonPanel item={item} />
                </div>
              ))
            )}
          </div>
        )}
        {activeTab === 'evidence' && <ReceptionDifferenceEvidencePanel evidence={c.evidence ?? []} />}
        {activeTab === 'responsibilities' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Responsables</h3>
            {proposedParties.length === 0 ? (
              <p className="text-xs text-slate-400">No hay responsables asignados.</p>
            ) : (
              proposedParties.map((p: ReceptionDifferenceResponsibleParty) => (
                <div key={p.responsibility_id} className="rounded-lg border border-slate-200 p-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800">{p.party_name}</span>
                    <span className="text-slate-500">{p.role} · {p.percentage ?? '—'}%</span>
                  </div>
                  {p.rationale && <p className="mt-1 text-slate-600">{p.rationale}</p>}
                  <button
                    type="button"
                    onClick={() => setDisputeParty(p)}
                    className="mt-2 rounded border border-rose-200 px-2 py-1 text-[10px] font-semibold text-rose-600 hover:bg-rose-50"
                  >
                    Disputar
                  </button>
                </div>
              ))
            )}
          </div>
        )}
        {activeTab === 'reviews' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Revisiones ({reviewsList.length})</h3>
            {reviewsList.length === 0 ? (
              <p className="text-xs text-slate-400">No hay revisiones registradas.</p>
            ) : (
              reviewsList.map((r: any) => (
                <div key={r.review_id || r.id} className="rounded-lg border border-slate-200 p-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800">{r.reviewer?.display_name ?? r.reviewer_name ?? '—'}</span>
                    <span className="text-[10px] text-slate-400">{r.created_at}</span>
                  </div>
                  <p className="text-slate-500">{r.decision === 'APPROVE' ? 'Aprobado' : r.decision === 'REQUEST_CHANGES' ? 'Cambios solicitados' : 'Rechazado'}</p>
                  {r.comment && <p className="mt-1 text-slate-600">{r.comment}</p>}
                  {r.changes_description && <p className="mt-1 text-amber-600">Cambios: {r.changes_description}</p>}
                </div>
              ))
            )}
          </div>
        )}
        {activeTab === 'approvals' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Aprobaciones ({approvalsList.length})</h3>
            {approvalsList.length === 0 ? (
              <p className="text-xs text-slate-400">No hay aprobaciones registradas.</p>
            ) : (
              approvalsList.map((a: any) => (
                <div key={a.approval_id || a.id} className="rounded-lg border border-slate-200 p-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800">{a.approved_by?.display_name ?? a.approver_name ?? '—'}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${a.decision === 'APPROVE' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                      {a.decision === 'APPROVE' ? 'APROBADO' : 'RECHAZADO'}
                    </span>
                  </div>
                  {a.comment && <p className="mt-1 text-slate-600">{a.comment}</p>}
                </div>
              ))
            )}
          </div>
        )}
        {activeTab === 'acknowledgements' && <ReceptionDifferenceAcknowledgementPanel acknowledgements={acksList} />}
        {activeTab === 'document' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Documento DIF</h3>
            {issuedDocs.length === 0 && pendingDocs.length === 0 ? (
              <p className="text-xs text-slate-400">No hay documentos emitidos ni pendientes.</p>
            ) : (
              <>
                {issuedDocs.map((d: any) => (
                  <div key={d.document_id || d.id} className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-emerald-800">{d.title ?? 'Documento DIF'}</span>
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">EMITIDO</span>
                    </div>
                    <p className="text-emerald-600">{d.version ?? 'v1.0'} · {d.generated_at ?? d.issued_at ?? ''}</p>
                  </div>
                ))}
                {pendingDocs.map((d: any) => (
                  <div key={d.document_id || d.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
                    <p className="font-semibold text-slate-700">{d.title ?? 'Documento DIF'}</p>
                    <p className="text-slate-500">Estado: {d.status}</p>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
        {activeTab === 'followup' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Preparación futura</h3>
            {c.future_preparation?.quarantine_recommendations && (
              <FutureQuarantineRecommendationsPanel recommendations={c.future_preparation.quarantine_recommendations} />
            )}
            {c.future_preparation?.claim_preparation && (
              <FutureClaimPreparationPanel preparation={c.future_preparation.claim_preparation} />
            )}
            {c.future_preparation?.quality_inspection_preparation && (
              <QualityInspectionPreparationPanel preparation={c.future_preparation.quality_inspection_preparation} />
            )}
          </div>
        )}
        {activeTab === 'integrity' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Integridad</h3>
            <div className="rounded-lg border border-slate-200 p-3 text-xs">
              <InfoRow label="Estado" value={c.integrity_status ?? '—'} />
              {c.content_hash && <InfoRow label="Hash SHA-256" value={c.content_hash} />}
              {c.integrity_checked_at && <InfoRow label="Verificado" value={c.integrity_checked_at} />}
              <InfoRow label="Versiones" value={String(c.total_versions ?? 1)} />
            </div>
          </div>
        )}
        {activeTab === 'history' && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Historial</h3>
            {!c.history || c.history.length === 0 ? (
              <p className="text-xs text-slate-400">No hay eventos en el historial.</p>
            ) : (
              <div className="space-y-2">
                {c.history.map((h: any) => (
                  <div key={h.history_id || h.id || Math.random()} className="rounded-lg border border-slate-200 p-3 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-800">{h.event_display || h.event_type}</span>
                      <span className="text-[10px] text-slate-400">{h.created_at || h.timestamp}</span>
                    </div>
                    <p className="text-slate-500">{h.event_description || h.action}</p>
                    {h.actor_display_name && <p className="text-slate-400">por {h.actor_display_name}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {showSubmitDialog && (
        <SubmitReceptionDifferenceCaseDialog
          caseData={c}
          _open={showSubmitDialog}
          onOpenChange={setShowSubmitDialog}
          onSuccess={() => caseQuery.refetch()}
        />
      )}

      {disputeParty && caseId && (
        <DisputeReceptionDifferenceDialog
          caseId={caseId}
          party={disputeParty}
          open={true}
          onOpenChange={(open) => { if (!open) setDisputeParty(null) }}
          onSuccess={() => { setDisputeParty(null); caseQuery.refetch() }}
        />
      )}
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-32 font-semibold text-slate-600">{label}:</span>
      <span className="text-slate-800">{value}</span>
    </div>
  )
}

function DifferenceItemCard({ item }: { item: ReceptionDifferenceItem }) {
  const level = item.difficulty_level ?? item.severity
  return (
    <div className="rounded-lg border border-slate-200 p-3 text-xs">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-800">{item.product.name}</span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
          level === 'HIGH' || level === 'CRITICAL'
            ? 'bg-rose-100 text-rose-700'
            : level === 'MEDIUM'
              ? 'bg-amber-100 text-amber-700'
              : 'bg-slate-100 text-slate-700'
        }`}>
          {level}
        </span>
      </div>
      <p className="text-slate-500">
        SKU: {item.product.sku} · Observado: {item.observed_quantity} {item.unit.symbol}
      </p>
      {item.description && <p className="mt-1 text-slate-600">{item.description}</p>}
      <ComparisonPanel item={item} />
    </div>
  )
}

function ComparisonPanel({ item }: { item: ReceptionDifferenceItem }) {
  switch (item.type) {
    case 'SHORTAGE':
      return <ShortageDifferencePanel item={item} />
    case 'OVERAGE':
      return <OverageDifferencePanel item={item} />
    case 'DAMAGE':
      return <DamageDifferencePanel item={item} />
    case 'WRONG_PRODUCT':
      return <WrongProductDifferencePanel item={item} />
    case 'MISSING_DOCUMENT':
      return <MissingDocumentDifferencePanel item={item} />
    case 'BROKEN_SEAL':
      return <BrokenSealDifferencePanel item={item} />
    default:
      return <p className="text-xs text-slate-400">Tipo de diferencia no soportado: {item.type}</p>
  }
}
