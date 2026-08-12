import { useState } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionEvidenceApi } from '../api/qualityInspectionEvidenceApi'
import type {
  QualityCertificateReview,
  QualityCertificateReviewStatus,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface QualityCertificateReviewPanelProps {
  inspectionId: string
  onCertificateUpdated: (review: QualityCertificateReview) => void
}

interface CertificateFormState {
  reviewId: string
  status: QualityCertificateReviewStatus
  fileId: string
  issuer: string
  referenceNumber: string
  issueDate: string
  expirationDate: string
  notes: string
}

export function QualityCertificateReviewPanel({
  inspectionId,
  onCertificateUpdated,
}: QualityCertificateReviewPanelProps) {
  const auth = useLogisticsPermissions()
  const canReview = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.reviewCertificate)
  const canUpload = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.uploadEvidence)

  const { data: evidenceData, isLoading, refetch } = useQuery<{ items: QualityCertificateReview[] }>(
    ['certificate-reviews', inspectionId],
    `/logistics/quality-inspection-evidence/evidence?inspection_id=${inspectionId}&evidence_type=CERTIFICATE`,
    undefined,
    { enabled: Boolean(inspectionId) },
  )

  const [editingReviewId, setEditingReviewId] = useState<string | null>(null)
  const [formState, setFormState] = useState<CertificateFormState>({
    reviewId: '',
    status: 'PENDING',
    fileId: '',
    issuer: '',
    referenceNumber: '',
    issueDate: '',
    expirationDate: '',
    notes: '',
  })
  const [error, setError] = useState<string | null>(null)

  const reviewMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionEvidenceApi.createLink(inspectionId, input as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1]),
    {
      onSuccess: (result) => {
        onCertificateUpdated(result as unknown as QualityCertificateReview)
        void refetch()
        setEditingReviewId(null)
        resetForm()
      },
      onError: (err) => {
        setError(err.message)
      },
    },
  )

  const certificates: QualityCertificateReview[] = evidenceData?.items ?? []

  function resetForm() {
    setFormState({
      reviewId: '',
      status: 'PENDING',
      fileId: '',
      issuer: '',
      referenceNumber: '',
      issueDate: '',
      expirationDate: '',
      notes: '',
    })
  }

  function startEdit(review: QualityCertificateReview) {
    setEditingReviewId(review.review_id)
    setFormState({
      reviewId: review.review_id,
      status: review.status,
      fileId: review.file?.file_id ?? '',
      issuer: review.issuer ?? '',
      referenceNumber: review.reference_number ?? '',
      issueDate: review.issue_date ?? '',
      expirationDate: review.expiration_date ?? '',
      notes: review.reviewer_notes ?? '',
    })
  }

  function handleSaveReview() {
    setError(null)
    void reviewMutation.mutate({
      review_id: formState.reviewId,
      status: formState.status,
      file_id: formState.fileId || undefined,
      issuer: formState.issuer || undefined,
      reference_number: formState.referenceNumber || undefined,
      issue_date: formState.issueDate || undefined,
      expiration_date: formState.expirationDate || undefined,
      reviewer_notes: formState.notes || undefined,
    } as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1])
  }

  function handleMarkMissing(reviewId: string) {
    setError(null)
    void reviewMutation.mutate({
      review_id: reviewId,
      status: 'MISSING',
    } as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1])
  }

  function handleMarkIllegible(reviewId: string) {
    setError(null)
    void reviewMutation.mutate({
      review_id: reviewId,
      status: 'ILLEGIBLE',
    } as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1])
  }

  function handleRequestReview(reviewId: string) {
    setError(null)
    void reviewMutation.mutate({
      review_id: reviewId,
      status: 'REVIEW_REQUESTED',
    } as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1])
  }

  function handleAssociateExisting(reviewId: string) {
    setEditingReviewId(reviewId)
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs space-y-4">
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-semibold text-sm text-slate-800">Revisión de certificados</h4>
        <StatusBadge value={certificates.length > 0 ? 'in_progress' : 'pending'} />
      </div>

      {isLoading ? (
        <div className="py-4 text-center text-slate-500">Cargando certificados…</div>
      ) : certificates.length === 0 ? (
        <Alert variant="info">No hay certificados para revisar en esta inspección.</Alert>
      ) : (
        <div className="space-y-3">
          {certificates.map((cert) => {
            const isEditing = editingReviewId === cert.review_id
            return (
              <div
                key={cert.review_id}
                className="rounded-lg border border-slate-200 p-3 space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-700">{cert.requirement_name ?? 'Certificado'}</span>
                      <StatusBadge value={cert.status.toLowerCase()} />
                    </div>
                    <div className="text-[11px] text-slate-500 space-y-0.5">
                      {cert.document_type && (
                        <div><span className="font-medium">Tipo: </span>{cert.document_type}</div>
                      )}
                      {cert.file && (
                        <div><span className="font-medium">Archivo: </span>{cert.file.filename}</div>
                      )}
                      {cert.issuer && (
                        <div><span className="font-medium">Emisor observado: </span>{cert.issuer}</div>
                      )}
                      {cert.issue_date && (
                        <div><span className="font-medium">Fecha emisión: </span>{cert.issue_date}</div>
                      )}
                      {cert.expiration_date && (
                        <div>
                          <span className="font-medium">Expiración: </span>{cert.expiration_date}
                          {cert.is_expired && <span className="text-rose-600 ml-1">(Vencido)</span>}
                          {cert.days_until_expiration !== null && cert.days_until_expiration !== undefined && (
                            <span className="text-slate-400 ml-1">({cert.days_until_expiration} días)</span>
                          )}
                        </div>
                      )}
                      {cert.reference_number && (
                        <div><span className="font-medium">Nº referencia: </span>{cert.reference_number}</div>
                      )}
                      <div>
                        <span className="font-medium">Match metadata: </span>
                        {cert.metadata_valid === true && <span className="text-emerald-600">Válido</span>}
                        {cert.metadata_valid === false && <span className="text-rose-600">Inválido</span>}
                        {cert.metadata_valid === null && <span className="text-slate-400">No evaluado</span>}
                      </div>
                      {cert.metadata_errors.length > 0 && (
                        <div className="text-rose-500">
                          Errores: {cert.metadata_errors.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {cert.reviewer_notes && (
                  <div className="rounded bg-slate-50 p-2 text-[11px] text-slate-600">
                    <span className="font-medium">Observación: </span>{cert.reviewer_notes}
                  </div>
                )}

                {isEditing && (
                  <div className="space-y-2 border-t border-slate-200 pt-2">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="field__label text-xs" htmlFor={`cert-status-${cert.review_id}`}>Estado</label>
                        <select
                          id={`cert-status-${cert.review_id}`}
                          className="field__input text-xs"
                          value={formState.status}
                          onChange={(e) => setFormState((prev) => ({ ...prev, status: e.target.value as QualityCertificateReviewStatus }))}
                        >
                          <option value="PENDING">Pendiente</option>
                          <option value="UPLOADED">Subido</option>
                          <option value="VERIFIED">Verificado</option>
                          <option value="MISSING">Faltante</option>
                          <option value="ILLEGIBLE">Ilegible</option>
                          <option value="REVIEW_REQUESTED">Revisión solicitada</option>
                        </select>
                      </div>
                      <Input
                        id={`cert-file-${cert.review_id}`}
                        label="File ID"
                        value={formState.fileId}
                        onChange={(e) => setFormState((prev) => ({ ...prev, fileId: e.target.value }))}
                        placeholder="ID del archivo"
                      />
                      <Input
                        id={`cert-issuer-${cert.review_id}`}
                        label="Emisor"
                        value={formState.issuer}
                        onChange={(e) => setFormState((prev) => ({ ...prev, issuer: e.target.value }))}
                        placeholder="Nombre del emisor"
                      />
                      <Input
                        id={`cert-ref-${cert.review_id}`}
                        label="Nº referencia"
                        value={formState.referenceNumber}
                        onChange={(e) => setFormState((prev) => ({ ...prev, referenceNumber: e.target.value }))}
                        placeholder="Número de referencia"
                      />
                      <Input
                        id={`cert-issue-${cert.review_id}`}
                        label="Fecha emisión"
                        type="date"
                        value={formState.issueDate}
                        onChange={(e) => setFormState((prev) => ({ ...prev, issueDate: e.target.value }))}
                      />
                      <Input
                        id={`cert-exp-${cert.review_id}`}
                        label="Fecha expiración"
                        type="date"
                        value={formState.expirationDate}
                        onChange={(e) => setFormState((prev) => ({ ...prev, expirationDate: e.target.value }))}
                      />
                    </div>
                    <Input
                      id={`cert-notes-${cert.review_id}`}
                      label="Notas"
                      value={formState.notes}
                      onChange={(e) => setFormState((prev) => ({ ...prev, notes: e.target.value }))}
                      placeholder="Observaciones del revisor"
                    />
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="primary"
                        size="small"
                        onClick={handleSaveReview}
                        isLoading={reviewMutation.isPending}
                        disabled={reviewMutation.isPending}
                      >
                        Guardar
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="small"
                        onClick={() => { setEditingReviewId(null); resetForm() }}
                      >
                        Cancelar
                      </Button>
                    </div>
                  </div>
                )}

                {!isEditing && canReview && (
                  <div className="flex flex-wrap gap-1.5">
                    <Button
                      type="button"
                      variant="ghost"
                      size="small"
                      onClick={() => startEdit(cert)}
                    >
                      Asociar archivo
                    </Button>
                    {canUpload && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="small"
                        onClick={() => handleAssociateExisting(cert.review_id)}
                      >
                        Subir archivo
                      </Button>
                    )}
                    <Button
                      type="button"
                      variant="ghost"
                      size="small"
                      onClick={() => handleMarkMissing(cert.review_id)}
                    >
                      Marcar faltante
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="small"
                      onClick={() => handleMarkIllegible(cert.review_id)}
                    >
                      Marcar ilegible
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="small"
                      onClick={() => handleRequestReview(cert.review_id)}
                    >
                      Solicitar revisión
                    </Button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {error && <Alert variant="error">{error}</Alert>}
    </div>
  )
}
