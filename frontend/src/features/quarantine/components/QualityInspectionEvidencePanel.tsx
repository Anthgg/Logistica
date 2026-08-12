import { useState } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionEvidenceApi } from '../api/qualityInspectionEvidenceApi'
import type {
  QualityInspectionEvidence,
  QualityInspectionControl,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface QualityInspectionEvidencePanelProps {
  inspectionId: string
  controls: QualityInspectionControl[]
  onEvidenceUploaded: (evidence: QualityInspectionEvidence) => void
}

const EVIDENCE_TYPES = [
  { value: 'PRODUCT', label: 'Producto' },
  { value: 'PACKAGING', label: 'Empaque' },
  { value: 'LABEL', label: 'Etiqueta' },
  { value: 'SCALE', label: 'Báscula' },
  { value: 'THERMOMETER', label: 'Termómetro' },
  { value: 'CERTIFICATE', label: 'Certificado' },
  { value: 'SAMPLE', label: 'Muestra' },
  { value: 'QUARANTINE_ZONE', label: 'Zona de cuarentena' },
  { value: 'SUPERVISOR_NOTE', label: 'Nota de supervisor' },
  { value: 'OTHER', label: 'Otro' },
] as const

interface UploadSessionState {
  uploadSessionId: string
  url: string
}

export function QualityInspectionEvidencePanel({
  inspectionId,
  controls,
  onEvidenceUploaded,
}: QualityInspectionEvidencePanelProps) {
  const auth = useLogisticsPermissions()
  const canUpload = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.uploadEvidence)

  const { data: evidenceData, isLoading, refetch } = useQuery<{ items: QualityInspectionEvidence[] }>(
    ['evidence', inspectionId],
    `/logistics/quality-inspection-evidence/evidence?inspection_id=${inspectionId}`,
    undefined,
    { enabled: Boolean(inspectionId) },
  )

  const [evidenceType, setEvidenceType] = useState<string>('OTHER')
  const [controlId, setControlId] = useState<string>('')
  const [classification, setClassification] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [tags, setTags] = useState<string>('')
  const [isSensitive, setIsSensitive] = useState<boolean>(false)
  const [fileId, setFileId] = useState<string>('')
  const [uploadSession, setUploadSession] = useState<UploadSessionState | null>(null)
  const [uploadingFile, setUploadingFile] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const createSessionMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionEvidenceApi.createUploadSession(inspectionId, input),
    {
      onSuccess: (result) => {
        setUploadSession(result as unknown as UploadSessionState)
      },
      onError: (err) => {
        setError(err.message)
      },
    },
  )

  const linkEvidenceMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionEvidenceApi.createLink(inspectionId, input as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1]),
    {
      onSuccess: (result) => {
        onEvidenceUploaded(result)
        void refetch()
        resetForm()
      },
      onError: (err) => {
        setError(err.message)
      },
    },
  )

  const archiveMutation = useMutation(
    (evidenceId: string) => qualityInspectionEvidenceApi.archive(evidenceId),
    {
      onSuccess: () => {
        void refetch()
      },
    },
  )

  const evidenceList: QualityInspectionEvidence[] = evidenceData?.items ?? []

  function resetForm() {
    setEvidenceType('OTHER')
    setControlId('')
    setClassification('')
    setDescription('')
    setTags('')
    setIsSensitive(false)
    setFileId('')
    setUploadSession(null)
    setUploadingFile(false)
  }

  function handleCreateUploadSession() {
    setError(null)
    void createSessionMutation.mutate({
      evidence_type: evidenceType,
      control_id: controlId || undefined,
    })
  }

  async function handleFileSelect(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file || !uploadSession) return

    setUploadingFile(true)
    setError(null)

    try {
      const response = await fetch(uploadSession.url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      })

      if (!response.ok) {
        throw new Error('Error al subir el archivo')
      }

      setFileId(uploadSession.uploadSessionId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al subir archivo')
    } finally {
      setUploadingFile(false)
    }
  }

  function handleLinkEvidence() {
    if (!fileId) return
    setError(null)

    const payload: Record<string, unknown> = {
      control_id: controlId || undefined,
      evidence_type: evidenceType,
      file_id: fileId,
      classification: classification || undefined,
      description: description || undefined,
      tags: tags ? tags.split(',').map((t) => t.trim()).filter(Boolean) : undefined,
      is_sensitive: isSensitive,
    }

    void linkEvidenceMutation.mutate(payload as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1])
  }

  function handleArchive(evidenceId: string) {
    void archiveMutation.mutate(evidenceId)
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs space-y-4">
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-semibold text-sm text-slate-800">Evidencia de inspección</h4>
        <StatusBadge value={evidenceList.length > 0 ? 'completed' : 'pending'} />
      </div>

      {isLoading ? (
        <div className="py-4 text-center text-slate-500">Cargando evidencia…</div>
      ) : (
        <>
          {evidenceList.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-[11px] font-semibold text-slate-600">Evidencia registrada ({evidenceList.length})</h5>
              <div className="max-h-48 overflow-y-auto space-y-2">
                {evidenceList.map((ev) => (
                  <div key={ev.evidence_id} className="rounded-lg border border-slate-200 p-2 space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <StatusBadge value={ev.evidence_type.toLowerCase().replace(/_/g, ' ')} />
                        <span className="font-medium">{ev.file?.filename ?? '—'}</span>
                      </div>
                      {canUpload && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="small"
                          onClick={() => handleArchive(ev.evidence_id)}
                          disabled={archiveMutation.isPending}
                        >
                          Archivar
                        </Button>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500 space-y-0.5">
                      {ev.classification && (
                        <div><span className="font-medium">Clasificación: </span>{ev.classification}</div>
                      )}
                      {ev.partial_hash && (
                        <div className="flex items-center gap-1">
                          <span className="font-medium">Hash parcial: </span>
                          <span className="font-mono text-[10px] text-slate-400">{ev.partial_hash}</span>
                        </div>
                      )}
                      {ev.anti_malware_status && (
                        <div className="flex items-center gap-1">
                          <span className="font-medium">Antimalware: </span>
                          <StatusBadge value={ev.anti_malware_status.toLowerCase()} />
                        </div>
                      )}
                      {ev.control_id && (
                        <div>
                          <span className="font-medium">Control: </span>
                          {controls.find((c) => c.control_id === ev.control_id)?.name ?? ev.control_id}
                        </div>
                      )}
                      {ev.description && (
                        <div><span className="font-medium">Descripción: </span>{ev.description}</div>
                      )}
                      {ev.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {ev.tags.map((tag) => (
                            <span key={tag} className="inline-flex items-center rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                      {ev.is_sensitive && (
                        <span className="inline-flex items-center gap-1 text-rose-600 font-medium">
                          <span className="h-1 w-1 rounded-full bg-rose-500" />
                          Sensible
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {evidenceList.length === 0 && (
            <Alert variant="info">No hay evidencia registrada aún.</Alert>
          )}

          {canUpload && (
            <div className="space-y-3 border-t border-slate-200 pt-3">
              <h5 className="text-[11px] font-semibold text-slate-600">Subir nueva evidencia</h5>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="field__label text-xs" htmlFor="ev-type">Tipo de evidencia</label>
                  <select
                    id="ev-type"
                    className="field__input text-xs"
                    value={evidenceType}
                    onChange={(e) => setEvidenceType(e.target.value)}
                  >
                    {EVIDENCE_TYPES.map((et) => (
                      <option key={et.value} value={et.value}>{et.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="field__label text-xs" htmlFor="ev-control">Control asociado</label>
                  <select
                    id="ev-control"
                    className="field__input text-xs"
                    value={controlId}
                    onChange={(e) => setControlId(e.target.value)}
                  >
                    <option value="">Ninguno</option>
                    {controls.map((c) => (
                      <option key={c.control_id} value={c.control_id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <Input
                  id="ev-classification"
                  label="Clasificación"
                  value={classification}
                  onChange={(e) => setClassification(e.target.value)}
                  placeholder="Clasificación del archivo"
                />

                <Input
                  id="ev-tags"
                  label="Etiquetas (separadas por coma)"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="etiqueta1, etiqueta2"
                />
              </div>

              <Input
                id="ev-description"
                label="Descripción"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Descripción de la evidencia"
              />

              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  checked={isSensitive}
                  onChange={(e) => setIsSensitive(e.target.checked)}
                  className="rounded border-slate-300"
                />
                Marcar como sensible
              </label>

              {!uploadSession ? (
                <Button
                  type="button"
                  variant="primary"
                  size="small"
                  onClick={handleCreateUploadSession}
                  isLoading={createSessionMutation.isPending}
                  disabled={createSessionMutation.isPending}
                >
                  Crear sesión de carga
                </Button>
              ) : (
                <div className="space-y-2">
                  <div className="rounded bg-emerald-50 border border-emerald-200 p-2 text-[11px] text-emerald-700">
                    Sesión de carga creada. Selecciona el archivo a subir.
                    <span className="block font-mono text-[10px] mt-1 text-emerald-600">
                      ID: {uploadSession.uploadSessionId}
                    </span>
                  </div>

                  <div>
                    <label className="field__label text-xs" htmlFor="ev-file">Archivo</label>
                    <input
                      id="ev-file"
                      type="file"
                      className="field__input text-xs"
                      onChange={handleFileSelect}
                      disabled={uploadingFile}
                    />
                    {uploadingFile && (
                      <span className="text-[11px] text-slate-500 mt-1">Subiendo archivo…</span>
                    )}
                  </div>

                  {fileId && (
                    <div className="rounded bg-blue-50 border border-blue-200 p-2 text-[11px] text-blue-700">
                      Archivo subido correctamente. Procesamiento y antimalware en curso.
                    </div>
                  )}

                  <Button
                    type="button"
                    variant="primary"
                    size="small"
                    onClick={handleLinkEvidence}
                    isLoading={linkEvidenceMutation.isPending}
                    disabled={!fileId || linkEvidenceMutation.isPending}
                  >
                    Vincular evidencia
                  </Button>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {error && <Alert variant="error">{error}</Alert>}
    </div>
  )
}
