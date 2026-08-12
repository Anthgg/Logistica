import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { filesApi } from '../api/files-api'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { PageHeader } from '../components/common/PageHeader'
import { Alert } from '../components/common/Alert'
import { SecureFileDropzone } from '../components/files/SecureFileDropzone'
import { FileUploadProgress } from '../components/files/FileUploadProgress'
import { LogisticsIcon } from '../components/common/LogisticsIcon'
import { getErrorMessage } from '../utils/errors'
import type {
  FileAssetType,
  FileClassification,
  FileUploadSession,
  FileUploadSessionRequest,
  FileUploadStatus,
} from '../types/files'

const ASSET_TYPES: { value: FileAssetType; label: string }[] = [
  { value: 'DOCUMENT', label: 'Documento' },
  { value: 'IMAGE', label: 'Imagen' },
  { value: 'PDF', label: 'PDF' },
  { value: 'XML', label: 'XML' },
  { value: 'SIGNATURE', label: 'Firma' },
  { value: 'PHOTO', label: 'Foto' },
  { value: 'EVIDENCE', label: 'Evidencia' },
  { value: 'OTHER', label: 'Otro' },
]

const CLASSIFICATIONS: { value: FileClassification; label: string }[] = [
  { value: 'INTERNAL', label: 'Interno' },
  { value: 'CONFIDENTIAL', label: 'Confidencial' },
  { value: 'RESTRICTED', label: 'Restringido' },
  { value: 'HIGHLY_RESTRICTED', label: 'Altamente restringido' },
]

const STEPS = ['Recurso', 'Archivo', 'Clasificar', 'Metadatos', 'Cargar', 'Resultado'] as const

export function FileUploadPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)

  // Step 1: Resource
  const [resourceType, setResourceType] = useState('')
  const [resourceId, setResourceId] = useState('')

  // Step 2: File
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  // Step 3: Classify
  const [assetType, setAssetType] = useState<FileAssetType>('DOCUMENT')
  const [classification, setClassification] = useState<FileClassification>('INTERNAL')

  // Step 4: Metadata
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [documentNumber, setDocumentNumber] = useState('')
  const [issuerName, setIssuerName] = useState('')

  // Step 5: Upload
  const [uploadSession, setUploadSession] = useState<FileUploadSession | null>(null)
  const [uploadStatus, setUploadStatus] = useState<FileUploadStatus>('PREPARING')
  const [progress, setProgress] = useState(0)
  const [loadedBytes, setLoadedBytes] = useState(0)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const [pollInterval, setPollInterval] = useState<ReturnType<typeof setInterval> | null>(null)

  // Step 6: Result
  const [fileAssetId, setFileAssetId] = useState<string | null>(null)

  const canProceed = () => {
    if (step === 0) return true
    if (step === 1) return selectedFile !== null
    if (step === 2) return Boolean(assetType && classification)
    if (step === 3) return title.trim().length > 0
    return true
  }
  void canProceed

  const startUpload = useCallback(async () => {
    if (!selectedFile) return
    setStep(4)
    setUploadStatus('PREPARING')
    setProgress(0)
    setUploadError(null)

    try {
      // 1. Create upload session
      setUploadStatus('AUTHORIZING')
      const request: FileUploadSessionRequest = {
        filename: selectedFile.name,
        size_bytes: selectedFile.size,
        declared_mime_type: selectedFile.type || 'application/octet-stream',
        asset_type: assetType,
        classification,
        resource_type: resourceType || undefined,
        resource_id: resourceId || undefined,
        metadata: {
          title: title.trim(),
          description: description.trim() || undefined,
          document_number: documentNumber.trim() || undefined,
          issuer_name: issuerName.trim() || undefined,
        },
      }
      const session = await filesApi.createUploadSession(request)
      setUploadSession(session)

      // 2. Upload to signed target
      setUploadStatus('UPLOADING')
      const controller = new AbortController()
      setAbortController(controller)

      await filesApi.uploadToSignedTarget(
        session.upload_target_url,
        session.upload_headers,
        session.method,
        selectedFile,
        (loaded, total) => {
          setLoadedBytes(loaded)
          setProgress(total > 0 ? (loaded / total) * 100 : 0)
        },
        controller.signal,
      )

      // 3. Finalize
      setUploadStatus('FINALIZING')
      const finalized = await filesApi.finalizeUploadSession(session.id)
      setUploadSession(finalized)

      // 4. Poll for processing
      setUploadStatus('ANALYZING')
      const poll = setInterval(async () => {
        try {
          const current = await filesApi.getUploadSession(session.id)
          setUploadStatus(current.status)
          if (current.file_asset_id) {
            setFileAssetId(current.file_asset_id)
          }
          if (current.status === 'AVAILABLE' || current.status === 'REJECTED' || current.status === 'QUARANTINED' || current.status === 'FAILED') {
            clearInterval(poll)
            setPollInterval(null)
            setStep(5)
          }
        } catch {
          // ignore poll errors
        }
      }, 3000)
      setPollInterval(poll)
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setUploadStatus('CANCELLED')
      } else {
        setUploadError(getErrorMessage(err))
        setUploadStatus('FAILED')
      }
    }
  }, [selectedFile, assetType, classification, resourceType, resourceId, title, description, documentNumber, issuerName])

  const cancelUpload = useCallback(() => {
    if (abortController) abortController.abort()
    if (uploadSession) void filesApi.abortUploadSession(uploadSession.id).catch(() => {})
    if (pollInterval) { clearInterval(pollInterval); setPollInterval(null) }
    setUploadStatus('CANCELLED')
  }, [abortController, uploadSession, pollInterval])

  const retryUpload = useCallback(() => {
    if (uploadSession) {
      void filesApi.retryUploadProcessing(uploadSession.id).then(() => {
        setUploadStatus('ANALYZING')
        const poll = setInterval(async () => {
          try {
            const current = await filesApi.getUploadSession(uploadSession.id)
            setUploadStatus(current.status)
            if (current.file_asset_id) setFileAssetId(current.file_asset_id)
            if (current.status === 'AVAILABLE' || current.status === 'REJECTED' || current.status === 'QUARANTINED' || current.status === 'FAILED') {
              clearInterval(poll)
              setPollInterval(null)
              setStep(5)
            }
          } catch { /* ignore */ }
        }, 3000)
        setPollInterval(poll)
      })
    }
  }, [uploadSession])

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <PageHeader
        title="Subir archivo"
        description="Carga segura de archivos al repositorio central"
        actions={<Button variant="ghost" onClick={() => navigate('/logistics/files')}>Cancelar</Button>}
      />

      {/* Step indicator */}
      <div className="flex items-center gap-1">
        {STEPS.map((s, idx) => (
          <div key={s} className="flex items-center">
            <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium ${
              idx === step ? 'bg-orange-500 text-white' : idx < step ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-500'
            }`}>{idx < step ? <LogisticsIcon name="check" size={14} aria-hidden /> : idx + 1}</div>
            {idx < STEPS.length - 1 && <div className={`h-0.5 w-12 ${idx < step ? 'bg-emerald-500' : 'bg-slate-200'}`} />}
          </div>
        ))}
      </div>

      {/* Step content */}
      {step === 0 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Recurso asociado (opcional)</h2>
          <p className="text-xs text-slate-400">Si el archivo corresponde a un recurso específico, indícalo. Puedes omitir este paso.</p>
          <Input label="Tipo de recurso" placeholder="business_partner, vehicle, driver..." value={resourceType} onChange={(e) => setResourceType(e.target.value)} />
          <Input label="ID del recurso" placeholder="UUID del recurso" value={resourceId} onChange={(e) => setResourceId(e.target.value)} />
          <div className="flex justify-end">
            <Button onClick={() => setStep(1)}>Siguiente</Button>
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Seleccionar archivo</h2>
          <SecureFileDropzone
            onFilesSelected={(files) => setSelectedFile(files[0] ?? null)}
            maxFiles={1}
            maxSizeBytes={100 * 1024 * 1024}
            label="Arrastra el archivo o haz clic para seleccionar"
            hint="PDF, XML, imágenes. Máximo 100 MB."
          />
          {selectedFile && (
            <div className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2 text-sm">
              <span className="font-medium text-slate-900">{selectedFile.name}</span>
              <span className="text-slate-400"> · {selectedFile.type || 'tipo desconocido'}</span>
            </div>
          )}
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep(0)}>Atrás</Button>
            <Button onClick={() => setStep(2)} disabled={!selectedFile}>Siguiente</Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Clasificar archivo</h2>
          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Tipo de asset</span>
            <select value={assetType} onChange={(e) => setAssetType(e.target.value as FileAssetType)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              {ASSET_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Clasificación de seguridad</span>
            <select value={classification} onChange={(e) => setClassification(e.target.value as FileClassification)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              {CLASSIFICATIONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </label>
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep(1)}>Atrás</Button>
            <Button onClick={() => setStep(3)}>Siguiente</Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Metadatos</h2>
          <Input label="Título" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Descripción (opcional)</span>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </label>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Número documental (opcional)" value={documentNumber} onChange={(e) => setDocumentNumber(e.target.value)} />
            <Input label="Emisor (opcional)" value={issuerName} onChange={(e) => setIssuerName(e.target.value)} />
          </div>
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep(2)}>Atrás</Button>
            <Button onClick={() => { setStep(4); void startUpload() }}>Revisar y cargar</Button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Cargando archivo</h2>
          {uploadError && <Alert variant="error">{uploadError}</Alert>}
          <FileUploadProgress
            status={uploadStatus}
            progress={progress}
            loadedBytes={loadedBytes}
            totalBytes={selectedFile?.size ?? 0}
            canCancel={uploadStatus === 'UPLOADING' || uploadStatus === 'AUTHORIZING' || uploadStatus === 'PREPARING'}
            canRetry={uploadStatus === 'FAILED' || uploadStatus === 'CANCELLED'}
            onCancel={cancelUpload}
            onRetry={retryUpload}
          />
          <div className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2 text-xs text-slate-500">
            <div>Archivo: {selectedFile?.name}</div>
            <div>Tipo: {assetType} · Clasificación: {classification}</div>
            <div>Título: {title}</div>
            {resourceType && <div>Recurso: {resourceType}:{resourceId}</div>}
          </div>
        </div>
      )}

      {step === 5 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Resultado</h2>
          {uploadStatus === 'AVAILABLE' && fileAssetId && (
            <div className="flex items-start gap-2 rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700">
              <LogisticsIcon name="check" size={16} className="mt-0.5 shrink-0" aria-hidden />
              Archivo disponible. El escaneo y validación se completaron correctamente.
            </div>
          )}
          {uploadStatus === 'QUARANTINED' && (
            <div className="flex items-start gap-2 rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
              <LogisticsIcon name="alert" size={16} className="mt-0.5 shrink-0" aria-hidden />
              El archivo fue puesto en cuarentena. Contacta al administrador.
            </div>
          )}
          {uploadStatus === 'REJECTED' && (
            <div className="flex items-start gap-2 rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
              <LogisticsIcon name="x" size={16} className="mt-0.5 shrink-0" aria-hidden />
              El archivo fue rechazado durante la validación.
            </div>
          )}
          {uploadStatus === 'FAILED' && (
            <div className="flex items-start gap-2 rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
              <LogisticsIcon name="x" size={16} className="mt-0.5 shrink-0" aria-hidden />
              La carga falló. Puedes reintentar.
            </div>
          )}
          {uploadStatus === 'CANCELLED' && (
            <div className="rounded-lg bg-slate-50 border border-slate-200 px-4 py-3 text-sm text-slate-500">
              Carga cancelada.
            </div>
          )}
          <div className="flex gap-3">
            {fileAssetId && (
              <Button onClick={() => navigate(`/logistics/files/${fileAssetId}`)}>Ver archivo</Button>
            )}
            <Button variant="ghost" onClick={() => navigate('/logistics/files')}>Volver al repositorio</Button>
          </div>
        </div>
      )}
    </div>
  )
}