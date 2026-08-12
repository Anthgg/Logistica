import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../common/Button'

export interface SessionExpiredDialogProps {
  isOpen: boolean
  onRedirect: () => void
}

export function SessionExpiredDialog({
  isOpen,
  onRedirect,
}: SessionExpiredDialogProps) {
  const navigate = useNavigate()
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return undefined

    const previousFocus = document.activeElement as HTMLElement | null
    cancelButtonRef.current?.focus()

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onRedirect()
      }
      if (event.key !== 'Tab') return

      const focusable = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), [href], [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      )
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable.at(-1)!
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      previousFocus?.focus()
    }
  }, [isOpen, onRedirect])

  if (!isOpen) return null

  const handleLogin = () => {
    navigate('/login', { replace: true })
    onRedirect()
  }

  return (
    <div className="dialog-backdrop" role="presentation">
      <div
        ref={dialogRef}
        className="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="session-expired-title"
        aria-describedby="session-expired-description"
      >
        <div className="dialog__icon dialog__icon--danger" aria-hidden="true">
          !
        </div>
        <h2 id="session-expired-title">Sesión expirada</h2>
        <div id="session-expired-description" className="dialog__description">
          <p>
            Tu sesión ha expirado. Serás redirigido al inicio de sesión para que
            puedas volver a autenticarte de forma segura.
          </p>
        </div>
        <div className="dialog__actions">
          <Button
            ref={cancelButtonRef}
            type="button"
            variant="primary"
            onClick={handleLogin}
          >
            Ir al inicio de sesión
          </Button>
        </div>
      </div>
    </div>
  )
}