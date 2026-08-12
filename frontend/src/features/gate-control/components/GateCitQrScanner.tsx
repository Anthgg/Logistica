import { useCallback, useEffect, useRef, useState } from 'react'

export interface GateCitQrScannerProps {
  onPayload: (payload: string) => void
  onCancel: () => void
}

/**
 * Escáner QR del CIT. Usa BarcodeDetector si está disponible, con fallback a
 * entrada manual accesible. No guarda la imagen del QR. No resuelve localmente.
 */
export function GateCitQrScanner({ onPayload, onCancel }: GateCitQrScannerProps) {
  const [manualValue, setManualValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [cameraActive, setCameraActive] = useState(false)
  const [detected, setDetected] = useState(false)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const rafRef = useRef<number | null>(null)
  const detectorRef = useRef<{ detect: (input: CanvasImageSource) => Promise<Array<{ rawValue: string }>> } | null>(null)

  const stop = useCallback(() => {
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
  }, [])

  useEffect(() => {
    return () => stop()
  }, [stop])

  const tick = useCallback(() => {
    if (!videoRef.current || !detectorRef.current) return
    const video = videoRef.current
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      detectorRef.current
        .detect(video)
        .then((results) => {
          if (results.length > 0 && results[0]?.rawValue) {
            setDetected(true)
            stop()
            onPayload(results[0].rawValue)
          }
        })
        .catch(() => {})
    }
    rafRef.current = requestAnimationFrame(tick)
  }, [onPayload, stop])

  const start = useCallback(async () => {
    setError(null)
    setDetected(false)
    try {
      // @ts-expect-error BarcodeDetector puede no existir en todos los navegadores
      const BarcodeDetectorCtor = window.BarcodeDetector
      if (BarcodeDetectorCtor) {
        detectorRef.current = new BarcodeDetectorCtor({ formats: ['qr_code'] })
      } else {
        setError('Tu navegador no soporta detección de QR. Usa la entrada manual.')
      }
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
      if (detectorRef.current) {
        rafRef.current = requestAnimationFrame(tick)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? `No se pudo acceder a la cámara: ${err.message}` : 'No se pudo acceder a la cámara.')
    }
  }, [tick])

  const handleManual = () => {
    const v = manualValue.trim()
    if (!v) return
    onPayload(v)
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <h3 className="text-sm font-bold text-slate-800">Escanear QR del CIT</h3>
      <p className="text-[11px] text-slate-500">No se guarda la imagen del QR. El payload se envía al backend.</p>

      {cameraActive && (
        <div>
          <video ref={videoRef} className="w-full rounded-lg bg-black" playsInline muted aria-label="Cámara para escanear QR" />
          {detected && <p className="mt-1 text-emerald-600">QR detectado.</p>}
        </div>
      )}

      {error && <p role="alert" className="rounded border border-rose-200 bg-rose-50 px-2 py-1 text-rose-700">{error}</p>}

      <div className="flex flex-wrap gap-2">
        {!cameraActive && (
          <button type="button" onClick={start} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 font-semibold text-white hover:bg-[#173a55]">
            Abrir cámara
          </button>
        )}
        {cameraActive && (
          <button type="button" onClick={stop} className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50">
            Detener cámara
          </button>
        )}
      </div>

      <div className="border-t border-slate-100 pt-3">
        <label htmlFor="qr-manual" className="mb-1 block font-bold text-slate-700">O introducir código/payload manualmente</label>
        <input
          id="qr-manual"
          type="text"
          value={manualValue}
          onChange={(e) => setManualValue(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
          autoComplete="off"
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleManual() } }}
        />
        <div className="mt-2 flex gap-2">
          <button type="button" onClick={handleManual} disabled={!manualValue.trim()} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
            Enviar
          </button>
          <button type="button" onClick={onCancel} className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}