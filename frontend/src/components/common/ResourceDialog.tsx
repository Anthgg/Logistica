import { useEffect, useRef, type FormEvent, type ReactNode } from 'react'
import { Button } from './Button'

export function ResourceDialog({
  isOpen,
  title,
  description,
  children,
  submitLabel,
  isSubmitting = false,
  isSubmitDisabled = false,
  onSubmit,
  onClose,
}: {
  isOpen: boolean
  title: string
  description?: string
  children: ReactNode
  submitLabel: string
  isSubmitting?: boolean
  isSubmitDisabled?: boolean
  onSubmit: () => void
  onClose: () => void
}) {
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return undefined

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isSubmitting) onClose()
      if (event.key !== 'Tab') return

      const focusable = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'input:not(:disabled), select:not(:disabled), textarea:not(:disabled), button:not(:disabled), [href], [tabindex]:not([tabindex="-1"])',
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

    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('keydown', handleKey)
    }
  }, [isOpen, isSubmitting, onClose])

  if (!isOpen) return null

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (isSubmitting || isSubmitDisabled) return
    onSubmit()
  }

  const close = () => {
    if (!isSubmitting) onClose()
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div
        ref={dialogRef}
        className="resource-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="resource-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Registro operativo</p>
            <h2 id="resource-dialog-title">{title}</h2>
            {description && <p>{description}</p>}
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={close}
            aria-label="Cerrar"
            disabled={isSubmitting}
          >
            ×
          </button>
        </div>
        <form onSubmit={submit}>
          <div className="resource-dialog__body">{children}</div>
          <div className="resource-dialog__footer">
            <Button type="button" variant="secondary" onClick={close} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={isSubmitting}
              loadingLabel="Guardando..."
              disabled={isSubmitDisabled || isSubmitting}
            >
              {isSubmitting ? 'Guardando...' : submitLabel}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
