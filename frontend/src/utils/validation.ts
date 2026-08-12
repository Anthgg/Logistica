export const MIN_PASSWORD_LENGTH = 12
export const MAX_PASSWORD_LENGTH = 128

export interface PasswordRequirements {
  minimumLength: boolean
  uppercase: boolean
  lowercase: boolean
  number: boolean
}

export function normalizeEmail(value: string): string {
  return value.trim().toLowerCase()
}

export function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizeEmail(value))
}

export function getPasswordRequirements(
  password: string,
): PasswordRequirements {
  return {
    minimumLength: password.length >= MIN_PASSWORD_LENGTH,
    uppercase: /[A-ZÁÉÍÓÚÑ]/.test(password),
    lowercase: /[a-záéíóúñ]/.test(password),
    number: /\d/.test(password),
  }
}

export function isStrongEnoughPassword(password: string): boolean {
  const requirements = getPasswordRequirements(password)
  return (
    password.length <= MAX_PASSWORD_LENGTH &&
    Object.values(requirements).every(Boolean)
  )
}
