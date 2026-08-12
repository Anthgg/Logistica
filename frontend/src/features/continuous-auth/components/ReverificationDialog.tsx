import {
  useEffect,
  useId,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent as ReactKeyboardEvent,
} from 'react'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { useContinuousAuth } from '../hooks/useContinuousAuth'
import { getContinuousAuthErrorMessage } from '../utils/continuous-auth-errors'

export function ReverificationDialog() {
  const {
    isReverificationOpen,
    isReverifying,
    authenticationLevel,
    riskLevel,
    reverify,
    closeReverification,
  } = useContinuousAuth()
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const returnFocusRef = useRef<HTMLElement | null>(null)
  const titleId = useId()
  const descriptionId = useId()
  const canCancel =
    authenticationLevel !== 'restricted' && riskLevel !== 'critical'

  useEffect(() => {
    if (!isReverificationOpen) {
      setPassword('')
      setShowPassword(false)
      setFormError(null)
      return undefined
    }

    returnFocusRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.setTimeout(() => passwordRef.current?.focus(), 0)

    return () => {
      document.body.style.overflow = previousOverflow
      returnFocusRef.current?.focus()
    }
  }, [isReverificationOpen])

  const handleKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape' && canCancel && !isReverifying) {
      closeReverification()
      return
    }

    if (event.key !== 'Tab' || !dialogRef.current) {
      return
    }

    const elements = dialogRef.current.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
    )
    const first = elements.item(0)
    const last = elements.item(elements.length - 1)

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last?.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first?.focus()
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!password || isReverifying) {
      return
    }

    setFormError(null)

    try {
      await reverify(password)
    } catch (error: unknown) {
      setFormError(getContinuousAuthErrorMessage(error))
    } finally {
      setPassword('')
    }
  }

  if (!isReverificationOpen) {
    return null
  }

  return (
    <div
      className="fixed inset-0 z-[80] grid place-items-center bg-slate-950/55 p-4 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          canCancel &&
          !isReverifying
        ) {
          closeReverification()
        }
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl"
        onKeyDown={handleKeyDown}
      >
        <div className="border-b border-slate-100 pb-4">
          <p className="text-xs font-bold uppercase tracking-wider text-blue-700">
            Control de seguridad
          </p>
          <h2 id={titleId} className="mt-1 text-xl font-bold text-slate-950">
            Confirma tu identidad
          </h2>
          <p id={descriptionId} className="mt-2 text-sm text-slate-600">
            Ingresa tu contraseña actual para recuperar el acceso a
            operaciones sensibles.
          </p>
        </div>

        <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
          <Input
            ref={passwordRef}
            label="Contraseña actual"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
            disabled={isReverifying}
            error={formError ?? undefined}
            endAdornment={
              <button
                type="button"
                className="min-h-9 px-2 text-xs font-semibold text-blue-700"
                onClick={() => setShowPassword((current) => !current)}
                aria-label={
                  showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'
                }
              >
                {showPassword ? 'Ocultar' : 'Mostrar'}
              </button>
            }
          />
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            {canCancel && (
              <Button
                type="button"
                variant="secondary"
                onClick={closeReverification}
                disabled={isReverifying}
              >
                Cancelar
              </Button>
            )}
            <Button
              type="submit"
              isLoading={isReverifying}
              disabled={!password}
            >
              Verificar identidad
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
