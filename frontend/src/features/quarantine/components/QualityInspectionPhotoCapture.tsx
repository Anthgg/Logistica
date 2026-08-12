import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionEvidenceApi } from '../api/qualityInspectionEvidenceApi'
import type { QualityInspectionEvidence } from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface QualityInspectionPhotoCaptureProps {
  inspectionId: string
  controlId?: string
  evidenceType?: string
  onPhotoCaptured: (evidence: QualityInspectionEvidence) => void
}

type CaptureStep =
  | 'idle'
  | 'requesting_camera'
  | 'camera_active'
  | 'preview'
  | 'creating_session'
  | 'uploading'
  | 'processing'
  | 'complete'
  | 'error'

export function QualityInspectionPhotoCapture({
  inspectionId,
  controlId,
  evidenceType = 'OTHER',
  onPhotoCaptured,
}: QualityInspectionPhotoCaptureProps) {
  const auth = useLogisticsPermissions()
  const canUpload = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.uploadEvidence)

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [step, setStep] = useState<CaptureStep>('idle')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null)
  const [uploadSession, setUploadSession] = useState<{ upload_session_id?: string; url?: string; upload_url?: string; file_id?: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const createSessionMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionEvidenceApi.createUploadSession(inspectionId, input),
    {
      onSuccess: (res) => {
        setUploadSession(res as { upload_session_id?: string; url?: string; upload_url?: string; file_id?: string })
        setStep('uploading')
      },
      onError: (err) => {
        setError(err.message)
        setStep('error')
      },
    },
  )

  const linkEvidenceMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionEvidenceApi.createLink(inspectionId, input as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1]),
    {
      onSuccess: (result) => {
        onPhotoCaptured(result)
        setStep('complete')
        releaseCamera()
      },
      onError: (err) => {
        setError(err.message)
        setStep('error')
      },
    },
  )

  function releaseCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
  }

  useEffect(() => {
    return () => {
      releaseCamera()
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const requestCamera = useCallback(async () => {
    setStep('requesting_camera')
    setError(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      })

      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }

      setStep('camera_active')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo acceder a la cámara')
      setStep('error')
    }
  }, [])

  function capturePhoto() {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.drawImage(video, 0, 0)

    canvas.toBlob(
      (blob) => {
        if (!blob) return
        const url = URL.createObjectURL(blob)
        setPreviewUrl(url)
        setCapturedBlob(blob)
        setStep('preview')
      },
      'image/jpeg',
      0.92,
    )
  }

  async function handleConfirmCapture() {
    if (!capturedBlob) return
    setStep('creating_session')

    await createSessionMutation.mutate({
      evidence_type: evidenceType,
      control_id: controlId || undefined,
      content_type: capturedBlob.type,
      filename: `photo-${Date.now()}.jpg`,
    } as Record<string, unknown>)
  }

  useEffect(() => {
    if (step !== 'uploading' || !capturedBlob) return

    let cancelled = false

    async function uploadFile() {
      const url = uploadSession?.url || uploadSession?.upload_url
      if (!url || !capturedBlob) return

      try {
        const response = await fetch(url, {
          method: 'PUT',
          body: capturedBlob,
          headers: { 'Content-Type': capturedBlob.type },
        })

        if (!response.ok || cancelled) {
          if (!cancelled) {
            setError('Error al subir la foto')
            setStep('error')
          }
          return
        }

        if (cancelled) return

        setStep('processing')

        await linkEvidenceMutation.mutate({
          control_id: controlId || undefined,
          evidence_type: evidenceType,
          file_id: uploadSession.upload_session_id || uploadSession.file_id,
          description: 'Foto capturada desde cámara',
        } as Parameters<typeof qualityInspectionEvidenceApi.createLink>[1])
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Error al subir')
          setStep('error')
        }
      }
    }

    void uploadFile()

    return () => {
      cancelled = true
    }
  }, [step, capturedBlob])

  function handleRetake() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(null)
    setCapturedBlob(null)
    setError(null)
    setStep('camera_active')

    if (videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current
      void videoRef.current.play()
    }
  }

  function handleDiscard() {
    releaseCamera()
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(null)
    setCapturedBlob(null)
    setError(null)
    setStep('idle')
  }

  if (!canUpload) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs">
        <Alert variant="warning">No tienes permiso para subir evidencia fotográfica.</Alert>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs space-y-3">
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-semibold text-sm text-slate-800">Captura de foto</h4>
        <StatusBadge value={step === 'complete' ? 'completed' : step === 'idle' ? 'pending' : 'in_progress'} />
      </div>

      <canvas ref={canvasRef} className="hidden" />

      {step === 'idle' && (
        <div className="space-y-2">
          <p className="text-[11px] text-slate-500">
            Toma una foto como evidencia de la inspección. La cámara se activará en modo trasero.
          </p>
          <Button
            type="button"
            variant="primary"
            size="small"
            onClick={requestCamera}
          >
            Solicitar cámara
          </Button>
        </div>
      )}

      {step === 'requesting_camera' && (
        <div className="py-4 text-center text-slate-500">
          Solicitando acceso a la cámara…
        </div>
      )}

      {step === 'camera_active' && (
        <div className="space-y-2">
          <div className="relative rounded-lg overflow-hidden bg-black aspect-video">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="primary"
              size="small"
              onClick={capturePhoto}
            >
              Capturar foto
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="small"
              onClick={handleDiscard}
            >
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {step === 'preview' && previewUrl && (
        <div className="space-y-2">
          <div className="relative rounded-lg overflow-hidden bg-black aspect-video">
            <img
              src={previewUrl}
              alt="Vista previa de la foto capturada"
              className="w-full h-full object-contain"
            />
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="primary"
              size="small"
              onClick={handleConfirmCapture}
              isLoading={createSessionMutation.isPending}
            >
              Confirmar y subir
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="small"
              onClick={handleRetake}
            >
              Tomar otra
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="small"
              onClick={handleDiscard}
            >
              Descartar
            </Button>
          </div>
        </div>
      )}

      {(step === 'creating_session' || step === 'uploading') && (
        <div className="py-4 text-center text-slate-500">
          {step === 'creating_session' ? 'Creando sesión de carga…' : 'Subiendo foto…'}
        </div>
      )}

      {step === 'processing' && (
        <div className="py-4 text-center text-slate-500">
          Procesando evidencia y verificando antimalware…
        </div>
      )}

      {step === 'complete' && (
        <Alert variant="success">
          Foto capturada y vinculada correctamente. Cámara liberada.
        </Alert>
      )}

      {step === 'error' && (
        <div className="space-y-2">
          <Alert variant="error">{error ?? 'Error desconocido'}</Alert>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="primary"
              size="small"
              onClick={handleRetake}
            >
              Reintentar
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="small"
              onClick={handleDiscard}
            >
              Descartar
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
