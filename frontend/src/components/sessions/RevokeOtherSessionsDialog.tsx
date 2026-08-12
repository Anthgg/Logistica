import { useEffect, useRef } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type { SessionSummary } from '../../types/session'

interface RevokeOtherSessionsDialogProps {
  isOpen: boolean
  sessions: SessionSummary[]
  isLoading: boolean
  onCancel: () => void
  onConfirm: () => void
}

export function RevokeOtherSessionsDialog({
  isOpen,
  sessions,
  isLoading,
  onCancel,
  onConfirm,
}: RevokeOtherSessionsDialogProps) {
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)

  const recentSessions = sessions.filter((s) => {
    const lastActivity = new Date(s.last_activity_at).getTime()
    const oneHourAgo = Date.now() - 60 * 60 * 1000
    return lastActivity > oneHourAgo
  })

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

  if (!isOpen) return null

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
        aria-labelledby="revoke-others-title"
        aria-describedby="revoke-others-desc"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="dialog__icon dialog__icon--danger" aria-hidden="true">
          <LogisticsIcon name="alert" size={22} />
        </div>
        <h2 id="revoke-others-title" className="text-base font-bold text-ink">
          ¿Cerrar todas las demás sesiones?
        </h2>
        <div id="revoke-others-desc" className="dialog__description mt-1.5">
          <p className="text-xs text-muted leading-relaxed">
            Se revocarán todas las sesiones excepto la que estás utilizando actualmente.
          </p>

          <div className="mt-3 rounded-lg border border-border-subtle bg-slate-50 p-3">
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Sesiones que se cerrarán</span>
              <span className="text-sm font-bold text-ink">{sessions.length}</span>
            </div>
            {recentSessions.length > 0 && (
              <div className="mt-2 flex items-start gap-1.5 border-t border-border-subtle pt-2">
                <LogisticsIcon name="alert" size={12} className="text-amber mt-0.5 shrink-0" />
                <p className="text-2xs text-amber">
                  {recentSessions.length} {recentSessions.length === 1 ? 'sesión tuvo actividad reciente' : 'sesiones tuvieron actividad reciente'} (última hora)
                </p>
              </div>
            )}
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
            loadingLabel="Cerrando…"
          >
            Cerrar otras sesiones
          </Button>
        </div>
      </div>
    </div>
  )
}