import { apiRequest, refreshAuthentication } from './api-client'
import { resetUnauthorizedNotification } from './auth-events'
import { clearCsrfToken } from './csrf'
import { ApiRequestError } from '../types/api'
import type {
  ActionResponse,
  AuthResponse,
  ChangePasswordRequest,
  LoginRequest,
  RegisterRequest,
} from '../types/auth'
import type { CurrentSession } from '../types/session'
import { USER_ROLES, type User, type UserRole } from '../types/user'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isNullableString(value: unknown): value is string | null {
  return typeof value === 'string' || value === null
}

function isUser(value: unknown): value is User {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    typeof value.email === 'string' &&
    typeof value.full_name === 'string' &&
    typeof value.role === 'string' &&
    USER_ROLES.includes(value.role as UserRole) &&
    typeof value.is_active === 'boolean' &&
    typeof value.is_verified === 'boolean' &&
    typeof value.created_at === 'string'
  )
}

function isCurrentSession(value: unknown): value is CurrentSession {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    typeof value.authentication_level === 'string' &&
    typeof value.created_at === 'string' &&
    typeof value.last_activity_at === 'string' &&
    typeof value.expires_at === 'string' &&
    isNullableString(value.device_id)
  )
}

function parseAuthResponse(value: unknown): AuthResponse {
  if (
    !isRecord(value) ||
    typeof value.success !== 'boolean' ||
    typeof value.message !== 'string' ||
    !isUser(value.user) ||
    !(value.session === null || isCurrentSession(value.session))
  ) {
    throw new ApiRequestError('El servidor devolvió datos de sesión inválidos.', {
      code: 'INVALID_RESPONSE',
    })
  }

  return value as unknown as AuthResponse
}

function parseActionResponse(value: unknown): ActionResponse {
  if (
    !isRecord(value) ||
    typeof value.success !== 'boolean' ||
    typeof value.message !== 'string' ||
    !(
      value.revoked_sessions === undefined ||
      value.revoked_sessions === null ||
      typeof value.revoked_sessions === 'number'
    )
  ) {
    throw new ApiRequestError('El servidor devolvió una respuesta inválida.', {
      code: 'INVALID_RESPONSE',
    })
  }

  return {
    success: value.success,
    message: value.message,
    revoked_sessions:
      typeof value.revoked_sessions === 'number'
        ? value.revoked_sessions
        : null,
  }
}

export async function register(
  payload: RegisterRequest,
): Promise<AuthResponse> {
  const response = await apiRequest<unknown>({
    path: '/auth/register',
    method: 'POST',
    body: payload,
  })
  return parseAuthResponse(response)
}

export async function login(payload: LoginRequest): Promise<AuthResponse> {
  const response = await apiRequest<unknown>({
    path: '/auth/login',
    method: 'POST',
    body: payload,
  })
  resetUnauthorizedNotification()
  return parseAuthResponse(response)
}

export async function getCurrentUser(): Promise<AuthResponse> {
  const response = await apiRequest<unknown>({
    path: '/auth/me',
    method: 'GET',
    requiresCsrf: false,
  })
  const parsedResponse = parseAuthResponse(response)
  resetUnauthorizedNotification()
  return parsedResponse
}

export async function refreshSession(): Promise<AuthResponse> {
  const response = await refreshAuthentication()
  return parseAuthResponse(response)
}

export async function logout(): Promise<ActionResponse> {
  const response = await apiRequest<unknown>({
    path: '/auth/logout',
    method: 'POST',
  })
  clearCsrfToken()
  return parseActionResponse(response)
}

export async function logoutAll(): Promise<ActionResponse> {
  const response = await apiRequest<unknown>({
    path: '/auth/logout-all',
    method: 'POST',
  })
  clearCsrfToken()
  return parseActionResponse(response)
}

export async function changePassword(
  payload: ChangePasswordRequest,
): Promise<ActionResponse> {
  const response = await apiRequest<unknown>({
    path: '/auth/change-password',
    method: 'POST',
    body: payload,
  })
  return parseActionResponse(response)
}
