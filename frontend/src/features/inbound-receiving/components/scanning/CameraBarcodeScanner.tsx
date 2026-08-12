import { useCallback, useEffect, useRef, useState } from 'react'

interface CameraBarcodeScannerProps {
  onScan: (code: string) => void
  onClose: () => void
  continuousDetection?: boolean
}

export function CameraBarcodeScanner({
  onScan,
  onClose,
  continuousDetection = false,
}: CameraBarcodeScannerProps) {
  const [error, setError] = useState<string | null>(null)
  const [cameraActive, setCameraActive] = useState(false)
  const [torchOn, setTorchOn] = useState(false)
  const [manualValue, setManualValue] = useState('')
  const [torchSupported, setTorchSupported] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const rafRef = useRef<number | null>(null)
  const detectorRef = useRef<{ detect: (input: CanvasImageSource) => Promise<Array<{ rawValue: string; format: string }>> } | null>(null)
  const lastDetectedRef = useRef('')

  const stopCamera = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) videoRef.current.srcObject = null
    setCameraActive(false)
    setTorchOn(false)
  }, [])

  useEffect(() => {
    return () => stopCamera()
  }, [stopCamera])

  const tick = useCallback(() => {
    if (!videoRef.current || !detectorRef.current) return
    const video = videoRef.current
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      detectorRef.current
        .detect(video)
        .then((results) => {
          if (results.length > 0 && results[0]?.rawValue) {
            const code = results[0].rawValue
            if (!continuousDetection && code === lastDetectedRef.current) return
            lastDetectedRef.current = code
            if (!continuousDetection) stopCamera()
            onScan(code)
          }
        })
        .catch(() => {})
    }
    rafRef.current = requestAnimationFrame(tick)
  }, [onScan, stopCamera, continuousDetection])

  const startCamera = useCallback(async () => {
    setError(null)
    try {
      // @ts-expect-error BarcodeDetector is not in all TS libs
      const BDCtor = window.BarcodeDetector
      if (BDCtor) {
        detectorRef.current = new BDCtor({
          formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'itf', 'qr_code', 'data_matrix'],
        })
      } else {
        setError('Tu navegador no soporta detección de códigos. Usa la entrada manual.')
        return
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {})
      }

      const track = stream.getVideoTracks()[0]
      if (track) {
        try {
          const caps = track.getCapabilities?.() as { torch?: boolean } | undefined
          setTorchSupported(caps?.torch === true)
        } catch {
          setTorchSupported(false)
        }
      }

      setCameraActive(true)
      rafRef.current = requestAnimationFrame(tick)
    } catch (err: unknown) {
      setError(err instanceof Error ? `No se pudo acceder a la cámara: ${err.message}` : 'No se pudo acceder a la cámara.')
    }
  }, [tick])

  const toggleTorch = useCallback(async () => {
    const track = streamRef.current?.getVideoTracks()[0]
    if (!track) return
    try {
      await track.applyConstraints({ advanced: [{ torch: !torchOn } as MediaTrackConstraintSet] })
      setTorchOn(!torchOn)
    } catch {
      // Torch not supported
    }
  }, [torchOn])

  const handleManualSubmit = () => {
    const v = manualValue.trim()
    if (!v) return
    onScan(v)
    setManualValue('')
    if (!continuousDetection) onClose()
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">Escaneo por cámara</h3>
        <button type="button" onClick={() => { stopCamera(); onClose() }} className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50">
          Cerrar
        </button>
      </div>

      {cameraActive && (
        <div className="relative overflow-hidden rounded-lg bg-black">
          <video ref={videoRef} className="w-full" playsInline muted aria-label="Cámara para escanear códigos" />
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <div className="h-32 w-64 rounded-lg border-2 border-white/50 md:h-24 md:w-48" />
          </div>
          <div className="absolute bottom-2 right-2 flex gap-1.5">
            {torchSupported && (
              <button type="button" onClick={() => void toggleTorch()} className="rounded-lg bg-black/60 px-2.5 py-1 text-xs font-semibold text-white">
                {torchOn ? 'Apagar linterna' : 'Linterna'}
              </button>
            )}
            <button type="button" onClick={stopCamera} className="rounded-lg bg-black/60 px-2.5 py-1 text-xs font-semibold text-white">
              Detener
            </button>
          </div>
        </div>
      )}

      {error && <p role="alert" className="rounded border border-rose-200 bg-rose-50 px-2 py-1 text-rose-700">{error}</p>}

      {!cameraActive && (
        <button type="button" onClick={() => void startCamera()} className="w-full rounded-lg bg-[#1F4E6D] px-3 py-2.5 font-semibold text-white hover:bg-[#173a55]">
          Abrir cámara
        </button>
      )}

      <div className="border-t border-slate-100 pt-3">
        <label htmlFor="camera-manual-input" className="mb-1 block font-bold text-slate-700">
          O introducir código manualmente
        </label>
        <div className="flex gap-2">
          <input
            id="camera-manual-input"
            type="text"
            value={manualValue}
            onChange={(e) => setManualValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleManualSubmit() } }}
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
            autoComplete="off"
          />
          <button type="button" onClick={handleManualSubmit} disabled={!manualValue.trim()} className="rounded-lg bg-[#1F4E6D] px-3 py-2 font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
            Enviar
          </button>
        </div>
      </div>
    </div>
  )
}
