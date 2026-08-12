import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errors'
import {
  getPasswordRequirements,
  isStrongEnoughPassword,
  isValidEmail,
  MAX_PASSWORD_LENGTH,
  MIN_PASSWORD_LENGTH,
  normalizeEmail,
} from '../utils/validation'

interface RegisterFormErrors {
  fullName?: string
  email?: string
  password?: string
  passwordConfirmation?: string
  acceptTerms?: string
}

export function RegisterPage() {
  const { register, authError, clearAuthError } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] = useState('')
  const [acceptTerms, setAcceptTerms] = useState(false)
  const [showPasswords, setShowPasswords] = useState(false)
  const [errors, setErrors] = useState<RegisterFormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const requirements = getPasswordRequirements(password)

  useEffect(() => {
    return () => clearAuthError()
  }, [clearAuthError])

  const validate = (): RegisterFormErrors => {
    const nextErrors: RegisterFormErrors = {}

    if (!fullName.trim()) {
      nextErrors.fullName = 'Ingresa tu nombre completo.'
    } else if (fullName.trim().length > 150) {
      nextErrors.fullName = 'El nombre no puede superar 150 caracteres.'
    }

    if (!email.trim()) {
      nextErrors.email = 'Ingresa tu correo.'
    } else if (!isValidEmail(email)) {
      nextErrors.email = 'Ingresa un correo válido.'
    }

    if (!isStrongEnoughPassword(password)) {
      nextErrors.password =
        `Usa entre ${MIN_PASSWORD_LENGTH} y ${MAX_PASSWORD_LENGTH} caracteres, ` +
        'con mayúscula, minúscula y número.'
    }

    if (!passwordConfirmation) {
      nextErrors.passwordConfirmation = 'Confirma tu contraseña.'
    } else if (password !== passwordConfirmation) {
      nextErrors.passwordConfirmation = 'Las contraseñas no coinciden.'
    }

    if (!acceptTerms) {
      nextErrors.acceptTerms = 'Debes aceptar los términos para continuar.'
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
      await register({
        full_name: fullName.trim(),
        email: normalizeEmail(email),
        password,
        password_confirmation: passwordConfirmation,
        accept_terms: acceptTerms,
      })
      setPassword('')
      setPasswordConfirmation('')
      navigate('/login', {
        replace: true,
        state: {
          message:
            'Tu cuenta fue creada correctamente. Ya puedes iniciar sesión.',
        },
      })
    } catch (error: unknown) {
      setSubmitError(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <div className="auth-card__heading">
        <p className="eyebrow">Nueva cuenta</p>
        <h2>Crea tu acceso</h2>
        <p>Completa tus datos para proteger tu cuenta.</p>
      </div>

      {(submitError ?? authError) && (
        <Alert variant="error">{submitError ?? authError}</Alert>
      )}

      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <Input
          label="Nombre completo"
          name="fullName"
          type="text"
          autoComplete="name"
          placeholder="Nombres y apellidos"
          value={fullName}
          onChange={(event) => {
            setFullName(event.target.value)
            setErrors((current) => ({ ...current, fullName: undefined }))
          }}
          error={errors.fullName}
          maxLength={150}
          disabled={isSubmitting}
        />
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
          type={showPasswords ? 'text' : 'password'}
          data-private-input="true"
          autoComplete="new-password"
          placeholder="Crea una contraseña segura"
          value={password}
          onChange={(event) => {
            setPassword(event.target.value)
            setErrors((current) => ({ ...current, password: undefined }))
          }}
          error={errors.password}
          maxLength={MAX_PASSWORD_LENGTH}
          disabled={isSubmitting}
          endAdornment={
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPasswords((value) => !value)}
              aria-label={
                showPasswords ? 'Ocultar contraseñas' : 'Mostrar contraseñas'
              }
              aria-pressed={showPasswords}
            >
              {showPasswords ? 'Ocultar' : 'Ver'}
            </button>
          }
          hint={
            <ul className="password-requirements">
              <li data-met={requirements.minimumLength}>
                {MIN_PASSWORD_LENGTH} caracteres
              </li>
              <li data-met={requirements.uppercase}>Una mayúscula</li>
              <li data-met={requirements.lowercase}>Una minúscula</li>
              <li data-met={requirements.number}>Un número</li>
            </ul>
          }
        />
        <Input
          label="Confirmar contraseña"
          name="passwordConfirmation"
          type={showPasswords ? 'text' : 'password'}
          data-private-input="true"
          autoComplete="new-password"
          placeholder="Repite tu contraseña"
          value={passwordConfirmation}
          onChange={(event) => {
            setPasswordConfirmation(event.target.value)
            setErrors((current) => ({
              ...current,
              passwordConfirmation: undefined,
            }))
          }}
          error={errors.passwordConfirmation}
          maxLength={MAX_PASSWORD_LENGTH}
          disabled={isSubmitting}
        />
        <div>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={acceptTerms}
              onChange={(event) => {
                setAcceptTerms(event.target.checked)
                setErrors((current) => ({
                  ...current,
                  acceptTerms: undefined,
                }))
              }}
              disabled={isSubmitting}
            />
            <span>Acepto los términos y el tratamiento de mis datos.</span>
          </label>
          {errors.acceptTerms && (
            <p className="checkbox-error" role="alert">
              {errors.acceptTerms}
            </p>
          )}
        </div>
        <Button
          type="submit"
          fullWidth
          isLoading={isSubmitting}
          disabled={isSubmitting}
        >
          Crear cuenta
        </Button>
      </form>

      <p className="auth-card__switch">
        ¿Ya tienes una cuenta? <Link to="/login">Iniciar sesión</Link>
      </p>
    </>
  )
}
