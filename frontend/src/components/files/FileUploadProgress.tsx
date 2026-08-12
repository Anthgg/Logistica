import { Button } from '../common/Button'
import { FileUploadStatusBadge } from './FileStatusBadge'
import { formatFileSize } from './file-utils'
import type { FileUploadStatus } from '../../types/files'

interface Props {
  status: FileUploadStatus
  progress: number
  loadedBytes: number
  totalBytes: number
  message?: string | null
  canCancel: boolean
  canRetry: boolean
  onCancel: () => void
  onRetry: () => void
}

export function FileUploadProgress({
  status,
  progress,
  loadedBytes,
  totalBytes,
  message,
  canCancel,
  canRetry,
  onCancel,
  onRetry,
}: Props) {
  const percent = Math.min(100, Math.round(progress))
  const isComplete = status === 'AVAILABLE' || status === 'REJECTED' || status === 'QUARANTINED' || status === 'FAILED' || status === 'CANCELLED'

  const barColor = status === 'QUARANTINED' || status === 'FAILED' || status === 'REJECTED'
    ? 'bg-rose-500'
    : status === 'AVAILABLE'
      ? 'bg-emerald-500'
      : 'bg-orange-500'

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3">
      <div className="flex items-center justify-between">
        <FileUploadStatusBadge status={status} />
        {!isComplete && (
          <span className="text-sm font-medium text-slate-700 tabular-nums">{percent}%</span>
        )}
      </div>

      {!isComplete && (
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
          <div
            className={`h-full rounded-full transition-colors duration-300 ${barColor}`}
            style={{ width: `${percent}%` }}
          />
        </div>
      )}

      {!isComplete && totalBytes > 0 && (
        <div className="flex justify-between text-xs text-slate-400">
          <span>{formatFileSize(loadedBytes)} / {formatFileSize(totalBytes)}</span>
          <span>Procesando...</span>
        </div>
      )}

      {message && (
        <p className="text-sm text-slate-500">{message}</p>
      )}

      <div className="flex gap-2">
        {canCancel && !isComplete && (
          <Button size="small" variant="ghost" onClick={onCancel}>Cancelar</Button>
        )}
        {canRetry && (status === 'FAILED' || status === 'CANCELLED') && (
          <Button size="small" onClick={onRetry}>Reintentar</Button>
        )}
      </div>

      {percent === 100 && status !== 'AVAILABLE' && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          Carga completada. Pendiente de escaneo y validación antes de estar disponible.
        </p>
      )}
    </div>
  )
}