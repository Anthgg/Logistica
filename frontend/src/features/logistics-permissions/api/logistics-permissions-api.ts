import { apiRequest } from '../../../api/api-client'
import { ApiRequestError } from '../../../types/api'
import type {
  AuthorizationCheckRequest,
  AuthorizationCheckResponse,
  LogisticsPermissionsResponse,
} from '../../../types/logistics-permissions'

const LOGISTICS_BOOTSTRAP_TIMEOUT_MS = 45_000

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isRoleScopeArray(
  value: unknown,
): value is LogisticsPermissionsResponse['roles'] {
  if (!Array.isArray(value)) return false
  return value.every(
    (item) =>
      isRecord(item) &&
      typeof item.role_code === 'string' &&
      typeof item.role_name === 'string' &&
      typeof item.scope_type === 'string' &&
      (item.organization_id === null ||
        typeof item.organization_id === 'string') &&
      (item.branch_id === null ||
        typeof item.branch_id === 'string') &&
      (item.warehouse_id === null ||
        typeof item.warehouse_id === 'string') &&
      (item.expires_at === null || typeof item.expires_at === 'string'),
  )
}

export function parsePermissionsResponse(
  value: unknown,
): LogisticsPermissionsResponse {
  if (
    !isRecord(value) ||
    typeof value.catalog_version !== 'string' ||
    typeof value.user_id !== 'string' ||
    !Array.isArray(value.permissions) ||
    !value.permissions.every((p) => typeof p === 'string') ||
    !Array.isArray(value.sensitive_permissions) ||
    !value.sensitive_permissions.every((p) => typeof p === 'string') ||
    !Array.isArray(value.step_up_permissions) ||
    !value.step_up_permissions.every((p) => typeof p === 'string') ||
    !isRoleScopeArray(value.roles)
  ) {
    throw new ApiRequestError(
      'La respuesta de permisos logísticos no es válida.',
      { code: 'INVALID_RESPONSE' },
    )
  }

  return {
    success: typeof value.success === 'boolean' ? value.success : true,
    catalog_version: value.catalog_version,
    user_id: value.user_id,
    permissions: value.permissions as string[],
    sensitive_permissions: value.sensitive_permissions as string[],
    step_up_permissions: value.step_up_permissions as string[],
    roles: value.roles as LogisticsPermissionsResponse['roles'],
  }
}

const PERMISSIONS_CACHE_KEY = 'logistics:permissions:me'

let inMemoryCache: LogisticsPermissionsResponse | null = null
let pendingRequest: Promise<LogisticsPermissionsResponse> | null = null

export function getPermissionsCacheKey(): string {
  return PERMISSIONS_CACHE_KEY
}

export function invalidatePermissionsCache(): void {
  inMemoryCache = null
  pendingRequest = null
}

export function getCachedPermissions(): LogisticsPermissionsResponse | null {
  return inMemoryCache
}

export async function getMyLogisticsPermissions(
  signal?: AbortSignal,
): Promise<LogisticsPermissionsResponse> {
  if (inMemoryCache) return inMemoryCache
  if (pendingRequest) return pendingRequest

  pendingRequest = apiRequest<unknown>({
    path: '/logistics/me/permissions',
    method: 'GET',
    requiresCsrf: false,
    signal,
    timeout: LOGISTICS_BOOTSTRAP_TIMEOUT_MS,
  })
    .then((payload) => {
      const parsed = parsePermissionsResponse(payload)
      inMemoryCache = parsed
      return parsed
    })
    .finally(() => {
      pendingRequest = null
    })

  return pendingRequest
}

export async function refreshMyLogisticsPermissions(
  signal?: AbortSignal,
): Promise<LogisticsPermissionsResponse> {
  invalidatePermissionsCache()
  return getMyLogisticsPermissions(signal)
}

export async function checkAuthorization(
  request: AuthorizationCheckRequest,
  signal?: AbortSignal,
): Promise<AuthorizationCheckResponse> {
  const payload = await apiRequest<unknown>({
    path: '/logistics/authorization/check',
    method: 'POST',
    body: request,
    signal,
  })

  if (
    !isRecord(payload) ||
    typeof payload.allowed !== 'boolean' ||
    typeof payload.permission_code !== 'string'
  ) {
    throw new ApiRequestError(
      'La respuesta de verificación de autorización no es válida.',
      { code: 'INVALID_RESPONSE' },
    )
  }

  return {
    success: typeof payload.success === 'boolean' ? payload.success : true,
    allowed: payload.allowed,
    permission_code: payload.permission_code,
    reason:
      payload.reason === null || typeof payload.reason === 'string'
        ? (payload.reason as string | null)
        : null,
  }
}
