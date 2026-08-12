import { useEffect, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage, isNetworkError } from '../utils/errors'
import { isValidEmail, normalizeEmail } from '../utils/validation'

interface LocationState {
  from?: {
    pathname?: string
    search?: string
  }
  message?: string
  errorMessage?: string
}

interface LoginFormErrors {
  email?: string
  password?: string
}

export function LoginPage() {
  const { login, authError, clearAuthError } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const locationState = location.state as LocationState | null
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<LoginFormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    return () => clearAuthError()
  }, [clearAuthError])

  const validate = (): LoginFormErrors => {
    const nextErrors: LoginFormErrors = {}

    if (!email.trim()) {
      nextErrors.email = 'Ingresa tu correo.'
    } else if (!isValidEmail(email)) {
      nextErrors.email = 'Ingresa un correo válido.'
    }

    if (!password) {
      nextErrors.password = 'Ingresa tu contraseña.'
    }

    return nextErrors
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (isSubmitting) {
      return
    }

    const nextErrors = validate()
    setErrors(nextErrors)
    setSubmitError(null)

    if (Object.keys(nextErrors).length > 0) {
      return
    }

    setIsSubmitting(true)

    try {
      await login({
        email: normalizeEmail(email),
        password,
        remember_me: rememberMe,
      })

      const destination = locationState?.from?.pathname
        ? `${locationState.from.pathname}${locationState.from.search ?? ''}`
        : '/profile'
      navigate(destination, { replace: true })
    } catch (error: unknown) {
      setSubmitError(
        isNetworkError(error)
          ? 'El servicio no está disponible en este momento. Revisa tu conexión e inténtalo nuevamente.'
          : getErrorMessage(error),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const visibleError =
    locationState?.errorMessage ?? submitError ?? authError

  return (
    <>
      <div className="auth-card__heading">
        <p className="eyebrow">Bienvenido</p>
        <h2>Inicia sesión</h2>
        <p>Accede al panel de seguridad de tu cuenta.</p>
      </div>

      {locationState?.message && (
        <Alert variant="success">{locationState.message}</Alert>
      )}
      {visibleError && <Alert variant="error">{visibleError}</Alert>}

      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <Input
          label="Correo electrónico"
          name="email"
          type="email"
          data-private-input="true"
          autoComplete="email"
          placeholder="nombre@correo.com"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value)
            setErrors((current) => ({ ...current, email: undefined }))
          }}
          error={errors.email}
          disabled={isSubmitting}
        />
        <Input
          label="Contraseña"
          name="password"
          type={showPassword ? 'text' : 'password'}
          data-private-input="true"
          autoComplete="current-password"
          placeholder="Ingresa tu contraseña"
          value={password}
          onChange={(event) => {
            setPassword(event.target.value)
            setErrors((current) => ({ ...current, password: undefined }))
          }}
          error={errors.password}
          disabled={isSubmitting}
          endAdornment={
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((value) => !value)}
              aria-label={
                showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'
              }
              aria-pressed={showPassword}
            >
              {showPassword ? 'Ocultar' : 'Ver'}
            </button>
          }
        />
        <label className="checkbox">
          <input
            type="checkbox"
            checked={rememberMe}
            onChange={(event) => setRememberMe(event.target.checked)}
            disabled={isSubmitting}
          />
          <span>Mantener mi sesión</span>
        </label>
        <Button
          type="submit"
          fullWidth
          isLoading={isSubmitting}
          disabled={isSubmitting}
        >
          Iniciar sesión
        </Button>
      </form>

      <p className="auth-card__switch">
        ¿Aún no tienes una cuenta? <Link to="/register">Crear cuenta</Link>
      </p>
      <p className="auth-card__privacy">
        Tus credenciales se envían mediante una conexión segura y nunca se
        guardan en este navegador.
      </p>
    </>
  )
}
