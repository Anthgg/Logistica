import { useCallback, useEffect, useRef, useState } from 'react'
import { gateEvidenceApi } from '../api/gateEvidenceApi'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { GatePhotoEvidenceType } from '../types/gate-control'
import { evidenceTypeLabel } from '../format'

type UploadState = 'IDLE' | 'CAPTURING' | 'UPLOADING' | 'PROCESSING' | 'DONE' | 'ERROR'

export interface SecureGatePhotoCaptureProps {
  checkInId: string
  evidenceType: GatePhotoEvidenceType
  classification?: string
  required?: boolean
  instructions?: string
  allowCamera?: boolean
  allowFile?: boolean
  maxFileSize?: number
  acceptedMimeTypes?: readonly string[]
  onAssociated?: (fileId: string) => void
}

/**
 * Captura fotográfica segura:
 * - No guarda base64 ni localStorage.
 * - Sube el Blob mediante upload session firmada del backend.
 * - Libera el stream de cámara al desmontar.
 * - No reconoce rostros ni aplica OCR.
 */
export function SecureGatePhotoCapture({
  checkInId,
  evidenceType,
  classification = 'OPERATIONAL',
  required = false,
  instructions,
  allowCamera = true,
  allowFile = true,
  maxFileSize = 10 * 1024 * 1024,
  acceptedMimeTypes = ['image/jpeg', 'image/png', 'image/webp'],
  onAssociated,
}: SecureGatePhotoCaptureProps) {
  const [state, setState] = useState<UploadState>('IDLE')
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [cameraActive, setCameraActive] = useState(false)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const previewUrlRef = useRef<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.gateControl.capturePhoto,
  })

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) videoRef.current.srcObject = null
    setCameraActive(false)
  }, [])

  const clearPreview = useCallback(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
      setPreviewUrl(null)
    }
  }, [])

  useEffect(() => {
    return () => {
      stopCamera()
      clearPreview()
      if (abortRef.current) abortRef.current.abort()
    }
  }, [stopCamera, clearPreview])

  const startCamera = useCallback(async () => {
    if (!allowCamera) return
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {})
      }
      setCameraActive(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? `No se pudo acceder a la cámara: ${err.message}` : 'No se pudo acceder a la cámara.')
    }
  }, [allowCamera])

  const uploadBlob = useCallback(
    async (blob: Blob, filename: string, mimeType: string) => {
      setState('UPLOADING')
      setError(null)
      setProgress(0)
      clearPreview()
      const url = URL.createObjectURL(blob)
      previewUrlRef.current = url
      setPreviewUrl(url)

      abortRef.current = new AbortController()
      try {
        const session = await gateEvidenceApi.createPhotoUploadSession(checkInId, {
          filename,
          size_bytes: blob.size,
          mime_type: mimeType,
          classification,
          evidence_type: evidenceType,
        })
        setState('UPLOADING')
        await gateEvidenceApi.uploadPhoto(
          session,
          blob,
          (loaded, total) => setProgress(total > 0 ? Math.round((loaded / total) * 100) : 0),
          abortRef.current.signal,
        )
        setState('PROCESSING')
        const finalized = await gateEvidenceApi.finalizeUpload(session.id)
        const fileId = finalized.file_asset_id
        if (!fileId) {
          throw new Error('El backend no devolvió el identificador del archivo.')
        }
        await gateEvidenceApi.associatePhoto(checkInId, { file_id: fileId, evidence_type: evidenceType })
        setState('DONE')
        onAssociated?.(fileId)
      } catch (err: unknown) {
        setState('ERROR')
        setError(err instanceof Error ? err.message : 'No se pudo subir la fotografía.')
      } finally {
        // El preview temporal se elimina tras asociar (no persiste).
        clearPreview()
      }
    },
    [checkInId, evidenceType, classification, clearPreview, onAssociated],
  )

  const capture = useCallback(async () => {
    if (!videoRef.current || !streamRef.current) return
    const video = videoRef.current
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 1280
    canvas.height = video.videoHeight || 720
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      setError('No se pudo procesar la imagen.')
      return
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const blob = await new Promise<Blob>((resolve) =>
      canvas.toBlob((b) => resolve(b as Blob), 'image/jpeg', 0.92),
    )
    stopCamera()
    void uploadBlob(blob, `${evidenceType}-${Date.now()}.jpg`, 'image/jpeg')
  }, [stopCamera, evidenceType, uploadBlob])

  const handleFile = useCallback(async (file: File) => {
    if (file.size > maxFileSize) {
      setError(`El archivo supera el tamaño máximo (${maxFileSize / 1024 / 1024} MB).`)
      return
    }
    if (!acceptedMimeTypes.includes(file.type)) {
      setError('Tipo de archivo no permitido.')
      return
    }
    void uploadBlob(file, file.name, file.type)
  }, [maxFileSize, acceptedMimeTypes, uploadBlob])

  const reset = useCallback(() => {
    setState('IDLE')
    setError(null)
    setProgress(0)
    clearPreview()
    stopCamera()
  }, [clearPreview, stopCamera])

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-semibold text-slate-700">{evidenceTypeLabel(evidenceType)}{required && <span className="ml-0.5 text-rose-500">*</span>}</span>
        {required && <span className="text-[11px] text-rose-600">Obligatoria</span>}
      </div>
      {instructions && <p className="mb-2 text-[11px] text-slate-500">{instructions}</p>}

      {guard.isBlocked && (
        <p className="mb-2 text-amber-600">Se requiere verificación reforzada para capturar.</p>
      )}

      {previewUrl && (
        <div className="mb-2">
          <img src={previewUrl} alt="Vista previa temporal" className="max-h-40 w-full rounded-lg object-cover" />
          <p className="mt-1 text-[11px] text-slate-400">Vista previa temporal. No se persiste en el navegador.</p>
        </div>
      )}

      {cameraActive && (
        <div className="mb-2">
          <video ref={videoRef} className="w-full rounded-lg bg-black" playsInline muted aria-label={`Cámara para ${evidenceTypeLabel(evidenceType)}`} />
        </div>
      )}

      {state === 'UPLOADING' && (
        <div className="mb-2">
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div className="h-2 bg-[#1F4E6D] transition-colors" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Subiendo… {progress}%</p>
        </div>
      )}
      {state === 'PROCESSING' && <p className="mb-2 text-[11px] text-slate-500">Procesando…</p>}
      {state === 'DONE' && <p className="mb-2 text-emerald-600">Fotografía asociada.</p>}
      {error && <p role="alert" className="mb-2 rounded border border-rose-200 bg-rose-50 px-2 py-1 text-rose-700">{error}</p>}

      <div className="flex flex-wrap gap-2">
        {allowCamera && state === 'IDLE' && !cameraActive && (
          <button type="button" onClick={startCamera} disabled={guard.isBlocked} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
            Abrir cámara
          </button>
        )}
        {cameraActive && (
          <>
            <button type="button" onClick={capture} className="rounded-lg bg-emerald-600 px-3 py-1.5 font-semibold text-white hover:bg-emerald-700">Capturar</button>
            <button type="button" onClick={stopCamera} className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
          </>
        )}
        {allowFile && state !== 'UPLOADING' && (
          <label className="cursor-pointer rounded-lg border border-slate-200 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50">
            Subir archivo
            <input type="file" accept={acceptedMimeTypes.join(',')} className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) void handleFile(f); e.target.value = '' }} />
          </label>
        )}
        {state === 'DONE' && (
          <button type="button" onClick={reset} className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50">Repetir</button>
        )}
      </div>
    </div>
  )
}