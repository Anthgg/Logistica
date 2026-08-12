import { useEffect, useRef } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { formatRelativeTime } from '../../utils/session-dates'
import { maskIpAddress } from '../../utils/date'
import type { SessionSummary } from '../../types/session'

interface RevokeSessionDialogProps {
  session: SessionSummary | null
  isOpen: boolean
  isLoading: boolean
  onCancel: () => void
  onConfirm: () => void
}

function safeText(value: string | null, fallback = 'No identificado'): string {
  return value && value.trim() !== '' ? value : fallback
}

export function RevokeSessionDialog({
  session,
  isOpen,
  isLoading,
  onCancel,
  onConfirm,
}: RevokeSessionDialogProps) {
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return undefined

    const previousFocus = document.activeElement as HTMLElement | null
    cancelButtonRef.current?.focus()

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isLoading) {
        onCancel()
      }
      if (event.key !== 'Tab') return

      const focusable = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), [href], [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      )
      const first = focusable[0]
      const last = focusable.at(-1)
      if (!first || !last) return

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
  }, [isLoading, isOpen, onCancel])

  if (!isOpen || !session) return null

  const isCurrent = session.is_current

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={() => { if (!isLoading) onCancel() }}
    >
      <div
        ref={dialogRef}
        className="dialog max-w-[420px] p-5 text-left"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="revoke-dialog-title"
        aria-describedby="revoke-dialog-desc"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="dialog__icon dialog__icon--danger" aria-hidden="true">
          <LogisticsIcon name="alert" size={22} />
        </div>
        <h2 id="revoke-dialog-title" className="text-base font-bold text-ink">
          {isCurrent ? '¿Cerrar la sesión actual?' : '¿Revocar esta sesión?'}
        </h2>
        <div id="revoke-dialog-desc" className="dialog__description mt-1.5">
          <p className="text-xs text-muted leading-relaxed">
            {isCurrent
              ? 'Saldrás de este dispositivo y deberás volver a iniciar sesión.'
              : 'El dispositivo perderá el acceso inmediatamente y deberá iniciar sesión nuevamente.'}
          </p>

          {/* Session summary */}
          <div className="mt-3 rounded-lg border border-border-subtle bg-slate-50 p-3 space-y-1.5">
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Navegador</span>
              <span className="text-2xs text-ink">{safeText(session.browser)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Sistema</span>
              <span className="text-2xs text-ink">{safeText(session.operating_system)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-2xs text-faint">IP</span>
              <span className="font-mono text-2xs text-ink">{maskIpAddress(session.ip_address)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Última actividad</span>
              <span className="text-2xs text-ink">{formatRelativeTime(session.last_activity_at)}</span>
            </div>
          </div>
        </div>
        <div className="dialog__actions mt-4">
          <Button
            ref={cancelButtonRef}
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            variant="danger"
            onClick={onConfirm}
            isLoading={isLoading}
            loadingLabel="Revocando…"
          >
            {isCurrent ? 'Cerrar sesión' : 'Revocar sesión'}
          </Button>
        </div>
      </div>
    </div>
  )
}