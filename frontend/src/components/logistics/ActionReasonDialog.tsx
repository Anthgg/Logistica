import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Button } from '../common/Button'
import { Input } from '../common/Input'

export interface ActionReasonDialogProps {
  isOpen: boolean
  title: string
  resourceLabel: string
  consequence?: ReactNode
  confirmLabel: string
  cancelLabel?: string
  isLoading?: boolean
  errorMessage?: string | null
  onConfirm: (reason: string) => void
  onCancel: () => void
}

const MIN_REASON_LENGTH = 1

export function ActionReasonDialog({
  isOpen,
  title,
  resourceLabel,
  consequence,
  confirmLabel,
  cancelLabel = 'Cancelar',
  isLoading = false,
  errorMessage = null,
  onConfirm,
  onCancel,
}: ActionReasonDialogProps) {
  const [reason, setReason] = useState('')
  const [touched, setTouched] = useState(false)
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const reasonId = 'action-reason-input'

  useEffect(() => {
    if (!isOpen) return undefined

    setReason('')
    setTouched(false)
    const previousFocus = document.activeElement as HTMLElement | null
    cancelButtonRef.current?.focus()

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isLoading) onCancel()
      if (event.key !== 'Tab') return

      const focusable = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), [href], input:not(:disabled), [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      )
      const firstFocusable = focusable[0]
      const lastFocusable = focusable.at(-1)
      if (!firstFocusable || !lastFocusable) return

      if (event.shiftKey && document.activeElement === firstFocusable) {
        event.preventDefault()
        lastFocusable.focus()
      } else if (!event.shiftKey && document.activeElement === lastFocusable) {
        event.preventDefault()
        firstFocusable.focus()
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      previousFocus?.focus()
    }
  }, [isLoading, isOpen, onCancel])

  if (!isOpen) return null

  const trimmed = reason.trim()
  const isValid = trimmed.length >= MIN_REASON_LENGTH
  const showError = touched && !isValid
  const descriptionId = 'action-reason-description'
  const errorId = 'action-reason-error'

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={() => {
        if (!isLoading) onCancel()
      }}
    >
      <div
        ref={dialogRef}
        className="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="action-reason-title"
        aria-describedby={descriptionId}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2 id="action-reason-title">{title}</h2>
        <div id={descriptionId} className="dialog__description">
          <p className="text-sm font-medium">{resourceLabel}</p>
          {consequence && (
            <p className="mt-1 text-sm text-slate-600">{consequence}</p>
          )}
        </div>

        <div className="mt-3">
          <Input
            id={reasonId}
            label="Motivo"
            value={reason}
            required
            autoFocus
            aria-invalid={showError}
            aria-describedby={showError ? errorId : undefined}
            placeholder="Describe el motivo de esta acción"
            onChange={(event) => setReason(event.target.value)}
            onBlur={() => setTouched(true)}
            disabled={isLoading}
          />
          {showError && (
            <p id={errorId} className="mt-1 text-sm text-rose-600" role="alert">
              Debes ingresar un motivo para continuar.
            </p>
          )}
          {errorMessage && (
            <p className="mt-2 text-sm text-rose-600" role="alert">
              {errorMessage}
            </p>
          )}
        </div>

        <div className="dialog__actions">
          <Button
            ref={cancelButtonRef}
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant="danger"
            onClick={() => {
              setTouched(true)
              if (isValid) onConfirm(trimmed)
            }}
            isLoading={isLoading}
            disabled={!isValid || isLoading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}