import { useEffect, useRef, useState } from 'react'
import { Button } from './Button'
import { LogisticsIcon } from './LogisticsIcon'

interface SecurePdfViewerProps {
  isOpen: boolean
  title: string
  code: string
  isVoided?: boolean
  reprintCount?: number
  fetchBlobUrl: () => Promise<string>
  onClose: () => void
  onDownload?: () => void
  onPrint?: () => void
}

export function SecurePdfViewer({
  isOpen,
  title,
  code,
  isVoided,
  reprintCount,
  fetchBlobUrl,
  onClose,
  onDownload,
  onPrint,
}: SecurePdfViewerProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const activeBlobUrlRef = useRef<string | null>(null)
  const fetchBlobUrlRef = useRef(fetchBlobUrl)
  fetchBlobUrlRef.current = fetchBlobUrl

  useEffect(() => {
    if (!isOpen) {
      if (activeBlobUrlRef.current) {
        URL.revokeObjectURL(activeBlobUrlRef.current)
        activeBlobUrlRef.current = null
      }
      setBlobUrl(null)
      setIsLoading(false)
      setError(null)
      return
    }

    let isMounted = true
    setIsLoading(true)
    setError(null)

    fetchBlobUrlRef
      .current()
      .then((url) => {
        if (!isMounted) {
          URL.revokeObjectURL(url)
          return
        }
        if (activeBlobUrlRef.current && activeBlobUrlRef.current !== url) {
          URL.revokeObjectURL(activeBlobUrlRef.current)
        }
        activeBlobUrlRef.current = url
        setBlobUrl(url)
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Error al cargar documento PDF')
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [isOpen])

  // Limpieza al desmontar el componente por completo
  useEffect(() => {
    return () => {
      if (activeBlobUrlRef.current) {
        URL.revokeObjectURL(activeBlobUrlRef.current)
        activeBlobUrlRef.current = null
      }
    }
  }, [])

  const handleDefaultDownload = () => {
    if (onDownload) {
      onDownload()
      return
    }
    if (blobUrl) {
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = `${code || 'documento'}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const handleDefaultPrint = () => {
    if (onPrint) {
      onPrint()
      return
    }
    if (blobUrl) {
      const printWindow = window.open(blobUrl, '_blank')
      if (printWindow) {
        printWindow.focus()
      }
    }
  }

  const handleOpenInNewTab = () => {
    if (blobUrl) {
      window.open(blobUrl, '_blank', 'noopener,noreferrer')
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/70 p-3 sm:p-6 backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="flex h-[90vh] w-full max-w-5xl flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden"
      >
        {/* Encabezado */}
        <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 font-bold">
              <LogisticsIcon name="document" size={18} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-sm font-bold text-slate-900 truncate">{title}</h2>
                <code className="rounded bg-slate-200 px-1.5 py-0.5 text-xs font-mono font-semibold text-slate-700">
                  {code}
                </code>
                {isVoided && (
                  <span className="rounded bg-rose-100 px-2 py-0.5 text-[10px] font-bold text-rose-700 uppercase tracking-wider">
                    ANULADO
                  </span>
                )}
                {reprintCount && reprintCount > 0 ? (
                  <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 uppercase tracking-wider">
                    REIMPRESIÓN N° {reprintCount}
                  </span>
                ) : null}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="small"
              variant="ghost"
              disabled={!blobUrl || isLoading}
              onClick={handleOpenInNewTab}
              title="Abrir en ventana independiente"
            >
              Abrir en pestaña
            </Button>
            <Button
              size="small"
              variant="ghost"
              disabled={!blobUrl || isLoading}
              onClick={handleDefaultPrint}
            >
              Imprimir
            </Button>
            <Button
              size="small"
              variant="secondary"
              disabled={!blobUrl || isLoading}
              onClick={handleDefaultDownload}
            >
              Descargar PDF
            </Button>
            <button
              type="button"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition-colors"
              onClick={onClose}
              aria-label="Cerrar visor"
            >
              <LogisticsIcon name="x" size={16} />
            </button>
          </div>
        </div>

        {/* Visor PDF Seguro */}
        <div className="relative flex-1 bg-slate-100 p-2 sm:p-4 overflow-hidden flex items-center justify-center">
          {isLoading && (
            <div className="flex flex-col items-center gap-3 text-xs text-slate-500">
              <span className="spinner" />
              <p>Cargando documento seguro…</p>
            </div>
          )}

          {error && (
            <div className="max-w-md rounded-xl border border-rose-200 bg-rose-50 p-4 text-center text-xs text-rose-700 space-y-2">
              <p className="font-bold">No se pudo desplegar la vista previa</p>
              <p>{error}</p>
              <Button size="small" variant="secondary" onClick={onClose} className="mt-2">
                Cerrar
              </Button>
            </div>
          )}

          {!isLoading && !error && blobUrl && (
            <div className="relative h-full w-full rounded-lg border border-slate-300 bg-white shadow-inner overflow-hidden">
              {isVoided && (
                <div className="aria-hidden pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-rose-500/10">
                  <span className="-rotate-45 select-none text-3xl sm:text-5xl font-extrabold uppercase tracking-widest text-rose-600/35 border-4 border-rose-600/35 px-6 py-3 rounded-2xl">
                    DOCUMENTO ANULADO
                  </span>
                </div>
              )}

              <iframe
                src={`${blobUrl}#toolbar=1&navpanes=0`}
                title={`Visor ${code}`}
                className="h-full w-full border-none"
              >
                <div className="flex h-full w-full flex-col items-center justify-center p-6 text-center text-slate-600 space-y-3">
                  <p className="font-medium text-sm">
                    El navegador no pudo incrustar la vista previa interactiva.
                  </p>
                  <div className="flex items-center gap-2">
                    <Button size="small" variant="primary" onClick={handleOpenInNewTab}>
                      Abrir PDF en pestaña
                    </Button>
                    <Button size="small" variant="secondary" onClick={handleDefaultDownload}>
                      Descargar archivo PDF
                    </Button>
                  </div>
                </div>
              </iframe>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
