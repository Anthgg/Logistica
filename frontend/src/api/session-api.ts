import { apiRequest } from './api-client'
import { ApiRequestError } from '../types/api'
import type { ActionResponse } from '../types/auth'
import type { SessionSummary, SessionsResponse } from '../types/session'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isNullableString(value: unknown): value is string | null {
  return typeof value === 'string' || value === null
}

function isSessionSummary(value: unknown): value is SessionSummary {
  return (
    isRecord(value) &&
    typeof value.id === 'string' &&
    isNullableString(value.device_name) &&
    isNullableString(value.browser) &&
    isNullableString(value.operating_system) &&
    isNullableString(value.device_type) &&
    isNullableString(value.ip_address) &&
    typeof value.created_at === 'string' &&
    typeof value.last_activity_at === 'string' &&
    typeof value.expires_at === 'string' &&
    typeof value.is_current === 'boolean'
  )
}

function parseSessionsResponse(value: unknown): SessionsResponse {
  if (
    !isRecord(value) ||
    typeof value.success !== 'boolean' ||
    !Array.isArray(value.sessions) ||
    !value.sessions.every(isSessionSummary)
  ) {
    throw new ApiRequestError('El listado de sesiones no es válido.', {
      code: 'INVALID_RESPONSE',
    })
  }

  return {
    success: value.success,
    sessions: value.sessions,
  }
}

function parseActionResponse(value: unknown): ActionResponse {
  if (
    !isRecord(value) ||
    typeof value.success !== 'boolean' ||
    typeof value.message !== 'string'
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

export async function listSessions(): Promise<SessionsResponse> {
  const response = await apiRequest<unknown>({
    path: '/auth/sessions',
    method: 'GET',
    requiresCsrf: false,
  })
  return parseSessionsResponse(response)
}

export const getSessions = listSessions

export async function revokeSession(
  sessionId: string,
): Promise<ActionResponse> {
  const response = await apiRequest<unknown>({
    path: `/auth/sessions/${encodeURIComponent(sessionId)}`,
    method: 'DELETE',
  })
  return parseActionResponse(response)
}
