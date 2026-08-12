import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { CancelReceptionDifferenceDocumentDialog } from '../components/CancelReceptionDifferenceDocumentDialog'
import type { ReceptionDifferenceCaseDetail, ReceptionDifferenceDocument } from '../types/reception-differences'

export default function ReceptionDifferenceDocumentPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const auth = useLogisticsPermissions()
  const [cancelDoc, setCancelDoc] = useState<ReceptionDifferenceDocument | null>(null)

  const { data: caseData, isLoading: loading, refetch } = useQuery<ReceptionDifferenceCaseDetail>(
    ['reception-difference-case', caseId],
    `/logistics/reception-difference-cases/${caseId}`,
    undefined,
    { enabled: !!caseId },
  )

  const canView = auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.view)
  const canIssue = auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.issueDIF || LOGISTICS_PERMISSIONS.receptionDifferences.approve)

  if (loading || !caseData) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-slate-500">
        {loading ? 'Cargando documento...' : 'Caso no encontrado'}
      </div>
    )
  }

  if (!canView) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-red-500">
        Sin permisos de visualización
      </div>
    )
  }

  const issuedDocuments: ReceptionDifferenceDocument[] = Array.isArray(caseData.documents)
    ? caseData.documents.filter((d: ReceptionDifferenceDocument) => d.status === 'ISSUED')
    : caseData.documents?.issued_documents ?? []

  const pendingDocuments: ReceptionDifferenceDocument[] = Array.isArray(caseData.documents)
    ? caseData.documents.filter((d: ReceptionDifferenceDocument) => d.status === 'PREVIEW' || d.status === 'NOT_ISSUED')
    : caseData.documents?.pending_documents ?? []

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-bold text-slate-800">Documento DIF — {caseData.case_code ?? caseData.case_id}</h1>
            <p className="text-xs text-slate-500">Documento único de diferencias de recepción</p>
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
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-bold text-slate-800">Información del caso</h2>
          <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
            <InfoCell label="Código" value={caseData.case_code ?? '—'} />
            <InfoCell label="Recepción" value={caseData.receiving_code ?? caseData.receipt_code ?? '—'} />
            <InfoCell label="Proveedor" value={caseData.supplier?.name ?? caseData.supplier_name ?? '—'} />
            <InfoCell label="Estado" value={caseData.current_status_display ?? caseData.status} />
          </div>
          {caseData.summary && (
            <p className="mt-3 text-xs text-slate-600">{caseData.summary}</p>
          )}
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-bold text-slate-800">Ítems de la diferencia ({caseData.items.length})</h2>
          <div className="space-y-2">
            {caseData.items.map((item) => (
              <div key={item.item_id} className="rounded-lg border border-slate-200 p-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800">{item.product.name}</span>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600">
                    {item.difficulty_level ?? item.severity}
                  </span>
                </div>
                <p className="text-slate-500">
                  SKU: {item.product.sku} · Observado: {item.observed_quantity} {item.unit.symbol}
                </p>
              </div>
            ))}
          </div>
        </section>

        {issuedDocuments.length > 0 && (
          <section className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-bold text-slate-800">Documentos emitidos</h2>
            <div className="space-y-2">
              {issuedDocuments.map((doc: ReceptionDifferenceDocument) => (
                <DocumentCard
                  key={doc.document_id}
                  document={doc}
                  canIssue={canIssue}
                  onCancel={() => setCancelDoc(doc)}
                />
              ))}
            </div>
          </section>
        )}

        {pendingDocuments.length > 0 && (
          <section className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-bold text-slate-800">Documentos pendientes</h2>
            <div className="space-y-2">
              {pendingDocuments.map((doc: ReceptionDifferenceDocument) => (
                <div key={doc.document_id} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
                  <p className="font-semibold text-slate-700">Documento pendiente</p>
                  <p className="text-slate-500">Estado: {doc.status}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {issuedDocuments.length === 0 && pendingDocuments.length === 0 && (
          <section className="rounded-xl border border-slate-200 bg-white p-8 text-center">
            <p className="text-xs text-slate-400">No hay documentos DIF emitidos ni pendientes para este caso.</p>
          </section>
        )}
      </div>

      {cancelDoc && caseId && (
        <CancelReceptionDifferenceDocumentDialog
          caseId={caseId}
          document={cancelDoc}
          open={true}
          onOpenChange={(open) => { if (!open) setCancelDoc(null) }}
          onSuccess={() => { setCancelDoc(null); refetch() }}
        />
      )}
    </div>
  )
}

function DocumentCard({ document, canIssue, onCancel }: { document: ReceptionDifferenceDocument; canIssue: boolean; onCancel: () => void }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3 text-xs">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-800">Documento DIF</span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
          (document.status as string) === 'ACTIVE' || document.status === 'ISSUED'
            ? 'bg-emerald-100 text-emerald-700'
            : 'bg-slate-100 text-slate-600'
        }`}>
          {document.status}
        </span>
      </div>
      <p className="text-slate-500">
        Caso: {document.case_code} · Emitido: {document.issued_at ?? '—'}
      </p>
      {document.pdf_url && (
        <p className="text-slate-400">PDF disponible</p>
      )}
      {canIssue && (
        <div className="mt-2 flex gap-2">
          {document.pdf_url && (
            <a
              href={document.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded border border-slate-200 px-2 py-1 text-[10px] font-semibold text-slate-600 hover:bg-slate-50"
            >
              Descargar PDF
            </a>
          )}
          <button
            type="button"
            onClick={onCancel}
            className="rounded border border-rose-200 px-2 py-1 text-[10px] font-semibold text-rose-600 hover:bg-rose-50"
          >
            Cancelar documento
          </button>
        </div>
      )}
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
