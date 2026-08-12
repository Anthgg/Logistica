import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { ConfirmDialog } from '../components/common/ConfirmDialog'
import { Input } from '../components/common/Input'
import { PageHeader } from '../components/common/PageHeader'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errors'
import {
  isStrongEnoughPassword,
  MAX_PASSWORD_LENGTH,
  MIN_PASSWORD_LENGTH,
} from '../utils/validation'

interface PasswordFormErrors {
  currentPassword?: string
  newPassword?: string
  confirmation?: string
}

export function SecurityPage() {
  const { changePassword, logoutAll } = useAuth()
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [logoutOtherSessions, setLogoutOtherSessions] = useState(true)
  const [showPasswords, setShowPasswords] = useState(false)
  const [formErrors, setFormErrors] = useState<PasswordFormErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  const [isLogoutAllDialogOpen, setIsLogoutAllDialogOpen] = useState(false)
  const [isLoggingOutAll, setIsLoggingOutAll] = useState(false)

  const validate = (): PasswordFormErrors => {
    const nextErrors: PasswordFormErrors = {}

    if (!currentPassword) {
      nextErrors.currentPassword = 'Ingresa tu contraseña actual.'
    }

    if (!isStrongEnoughPassword(newPassword)) {
      nextErrors.newPassword =
        `Usa entre ${MIN_PASSWORD_LENGTH} y ${MAX_PASSWORD_LENGTH} caracteres, ` +
        'con mayúscula, minúscula y número.'
    } else if (newPassword === currentPassword) {
      nextErrors.newPassword =
        'La nueva contraseña debe ser diferente de la actual.'
    }

    if (!confirmation) {
      nextErrors.confirmation = 'Confirma la nueva contraseña.'
    } else if (newPassword !== confirmation) {
      nextErrors.confirmation = 'Las contraseñas no coinciden.'
    }

    return nextErrors
  }

  const handlePasswordChange = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()
    if (isChangingPassword) {
      return
    }

    const nextErrors = validate()
    setFormErrors(nextErrors)
    setError(null)
    setSuccess(null)

    if (Object.keys(nextErrors).length > 0) {
      return
    }

    setIsChangingPassword(true)

    try {
      const response = await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirmation: confirmation,
        logout_other_sessions: logoutOtherSessions,
      })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmation('')
      setSuccess(
        response.message || 'Tu contraseña fue actualizada correctamente.',
      )
    } catch (caughtError: unknown) {
      setError(getErrorMessage(caughtError))
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleLogoutAll = async () => {
    if (isLoggingOutAll) {
      return
    }

    setIsLoggingOutAll(true)
    setError(null)

    try {
      await logoutAll()
      navigate('/login', {
        replace: true,
        state: {
          message: 'Todas las sesiones fueron cerradas correctamente.',
        },
      })
    } catch (caughtError: unknown) {
      setError(getErrorMessage(caughtError))
      setIsLogoutAllDialogOpen(false)
    } finally {
      setIsLoggingOutAll(false)
    }
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Protección de cuenta"
        title="Seguridad"
        description="Actualiza tus credenciales y controla todos los accesos a tu cuenta."
      />

      {error && (
        <Alert variant="error" onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" onDismiss={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <div className="security-grid">
        <section className="panel">
          <div className="panel__heading">
            <div>
              <p className="eyebrow">Credenciales</p>
              <h2>Cambiar contraseña</h2>
              <p>
                Usa una contraseña única que no utilices en otros servicios.
              </p>
            </div>
            <span className="panel__index" aria-hidden="true">
              01
            </span>
          </div>
          <form
            className="form-stack form-stack--security"
            onSubmit={handlePasswordChange}
            noValidate
          >
            <Input
              label="Contraseña actual"
              name="currentPassword"
              type={showPasswords ? 'text' : 'password'}
              data-private-input="true"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(event) => {
                setCurrentPassword(event.target.value)
                setFormErrors((current) => ({
                  ...current,
                  currentPassword: undefined,
                }))
              }}
              error={formErrors.currentPassword}
              maxLength={MAX_PASSWORD_LENGTH}
              disabled={isChangingPassword}
            />
            <Input
              label="Nueva contraseña"
              name="newPassword"
              type={showPasswords ? 'text' : 'password'}
              data-private-input="true"
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => {
                setNewPassword(event.target.value)
                setFormErrors((current) => ({
                  ...current,
                  newPassword: undefined,
                }))
              }}
              error={formErrors.newPassword}
              hint={`Mínimo ${MIN_PASSWORD_LENGTH} caracteres, con mayúscula, minúscula y número.`}
              maxLength={MAX_PASSWORD_LENGTH}
              disabled={isChangingPassword}
            />
            <Input
              label="Confirmar nueva contraseña"
              name="confirmation"
              type={showPasswords ? 'text' : 'password'}
              data-private-input="true"
              autoComplete="new-password"
              value={confirmation}
              onChange={(event) => {
                setConfirmation(event.target.value)
                setFormErrors((current) => ({
                  ...current,
                  confirmation: undefined,
                }))
              }}
              error={formErrors.confirmation}
              maxLength={MAX_PASSWORD_LENGTH}
              disabled={isChangingPassword}
            />
            <label className="checkbox">
              <input
                type="checkbox"
                checked={showPasswords}
                onChange={(event) => setShowPasswords(event.target.checked)}
                disabled={isChangingPassword}
              />
              <span>Mostrar contraseñas</span>
            </label>
            <label className="checkbox checkbox--boxed">
              <input
                type="checkbox"
                checked={logoutOtherSessions}
                onChange={(event) =>
                  setLogoutOtherSessions(event.target.checked)
                }
                disabled={isChangingPassword}
              />
              <span>
                <strong>Cerrar las demás sesiones</strong>
                <small>
                  Recomendado si sospechas que alguien conoce tu contraseña.
                </small>
              </span>
            </label>
            <div className="form-actions">
              <Button
                type="submit"
                isLoading={isChangingPassword}
                disabled={isChangingPassword}
              >
                Actualizar contraseña
              </Button>
            </div>
          </form>
        </section>

        <section className="panel panel--danger-zone">
          <div className="panel__heading">
            <div>
              <p className="eyebrow eyebrow--danger">Acción crítica</p>
              <h2>Cerrar todas las sesiones</h2>
              <p>
                Revoca el acceso de todos los dispositivos, incluido este.
              </p>
            </div>
            <span className="panel__index" aria-hidden="true">
              02
            </span>
          </div>
          <div className="danger-zone__body">
            <div className="danger-zone__symbol" aria-hidden="true">
              !
            </div>
            <p>
              Tendrás que iniciar sesión nuevamente en cada dispositivo. Esta
              acción no cambia tu contraseña.
            </p>
            <Button
              type="button"
              variant="danger"
              onClick={() => setIsLogoutAllDialogOpen(true)}
            >
              Cerrar todas las sesiones
            </Button>
          </div>
        </section>
      </div>

      <ConfirmDialog
        isOpen={isLogoutAllDialogOpen}
        title="¿Cerrar todas las sesiones?"
        description="Se revocará inmediatamente el acceso de todos los dispositivos, incluido este."
        confirmLabel="Cerrar todas"
        isLoading={isLoggingOutAll}
        onCancel={() => setIsLogoutAllDialogOpen(false)}
        onConfirm={() => void handleLogoutAll()}
      />
    </div>
  )
}
