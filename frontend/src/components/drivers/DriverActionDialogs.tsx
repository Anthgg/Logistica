import { useState } from 'react'
import { Button } from '../common/Button'

interface ActionDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel: string
  reasonLabel: string
  reasonPlaceholder?: string
  onConfirm: (reason: string) => Promise<void>
  onClose: () => void
  isDanger?: boolean
}

export function DriverActionDialog({
  open,
  title,
  description,
  confirmLabel,
  reasonLabel,
  reasonPlaceholder,
  onConfirm,
  onClose,
  isDanger,
}: ActionDialogProps) {
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!open) return null

  const handleConfirm = async () => {
    if (!reason.trim()) {
      setError('El motivo es obligatorio.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await onConfirm(reason.trim())
      setReason('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al procesar la acción.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    setReason('')
    setError(null)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm" onClick={handleClose}>
      <div
        className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-bold text-slate-100">{title}</h2>
        <p className="mt-2 text-sm text-slate-400 leading-relaxed">{description}</p>

        <label className="mt-4 flex flex-col gap-1">
          <span className="text-sm font-medium text-slate-200">{reasonLabel}</span>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            placeholder={reasonPlaceholder}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500"
            autoFocus
          />
        </label>

        {error && <div className="mt-3 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-sm text-rose-700">{error}</div>}

        <div className="mt-4 flex justify-end gap-3">
          <Button type="button" variant="ghost" onClick={handleClose} disabled={submitting}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant={isDanger ? 'danger' : 'primary'}
            onClick={handleConfirm}
            disabled={submitting || !reason.trim()}
            isLoading={submitting}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}

export function BlockDriverDialog(props: Omit<ActionDialogProps, 'title' | 'description' | 'confirmLabel' | 'reasonLabel' | 'isDanger'>) {
  return (
    <DriverActionDialog
      {...props}
      title="Bloquear conductor"
      description="El conductor no podrá operar hasta que sea desbloqueado. Esta acción requiere confirmación reforzada."
      confirmLabel="Bloquear"
      reasonLabel="Motivo del bloqueo"
      reasonPlaceholder="Describe el motivo del bloqueo..."
      isDanger
    />
  )
}

export function SuspendDriverDialog(props: Omit<ActionDialogProps, 'title' | 'description' | 'confirmLabel' | 'reasonLabel' | 'isDanger'>) {
  return (
    <DriverActionDialog
      {...props}
      title="Suspender conductor"
      description="El conductor será suspendido temporalmente. Podrá ser reactivado posteriormente."
      confirmLabel="Suspender"
      reasonLabel="Motivo de la suspensión"
      reasonPlaceholder="Describe el motivo de la suspensión..."
      isDanger
    />
  )
}

export function RetireDriverDialog(props: Omit<ActionDialogProps, 'title' | 'description' | 'confirmLabel' | 'reasonLabel' | 'isDanger'>) {
  return (
    <DriverActionDialog
      {...props}
      title="Retirar conductor"
      description="El conductor será retirado del sistema. Esta acción es permanente y requiere confirmación reforzada."
      confirmLabel="Retirar"
      reasonLabel="Motivo del retiro"
      reasonPlaceholder="Describe el motivo del retiro..."
      isDanger
    />
  )
}