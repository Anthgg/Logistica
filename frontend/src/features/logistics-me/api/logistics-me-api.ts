import { apiRequest } from '../../../api/api-client'
import { ApiRequestError } from '../../../types/api'
import type {
  LogisticsContextChangeRequest,
  LogisticsContextChangeResponse,
  LogisticsMeResponse,
} from '../../../types/logistics-me'

const LOGISTICS_BOOTSTRAP_TIMEOUT_MS = 45_000

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

export function parseLogisticsMeResponse(value: unknown): LogisticsMeResponse {
  if (!isRecord(value)) {
    throw new ApiRequestError('La respuesta de /logistics/me no es válida.', {
      code: 'INVALID_RESPONSE',
    })
  }

  const user = value.user
  if (
    !isRecord(user) ||
    typeof user.id !== 'string' ||
    typeof user.display_name !== 'string' ||
    typeof user.email !== 'string' ||
    typeof user.platform_role !== 'string' ||
    typeof user.is_active !== 'boolean'
  ) {
    throw new ApiRequestError('El usuario logístico no es válido.', {
      code: 'INVALID_RESPONSE',
    })
  }

  const session = value.session
  if (
    !isRecord(session) ||
    typeof session.id !== 'string' ||
    typeof session.expires_at !== 'string' ||
    typeof session.authentication_level !== 'string'
  ) {
    throw new ApiRequestError('La sesión logística no es válida.', {
      code: 'INVALID_RESPONSE',
    })
  }

  const logistics = value.logistics
  if (
    !isRecord(logistics) ||
    typeof logistics.enabled !== 'boolean' ||
    !isStringArray(logistics.roles) ||
    !isStringArray(logistics.permissions) ||
    !isStringArray(logistics.sensitive_permissions) ||
    !isStringArray(logistics.step_up_permissions) ||
    !isStringArray(logistics.organizations) ||
    !isStringArray(logistics.branches) ||
    !isStringArray(logistics.warehouses)
  ) {
    throw new ApiRequestError('El contexto logístico no es válido.', {
      code: 'INVALID_RESPONSE',
    })
  }

  return {
    success: typeof value.success === 'boolean' ? value.success : true,
    user: {
      id: user.id,
      display_name: user.display_name,
      email: user.email,
      platform_role: user.platform_role,
      is_active: user.is_active,
    },
    session: {
      id: session.id,
      device_id: typeof session.device_id === 'string' ? session.device_id : null,
      expires_at: session.expires_at,
      authentication_level: session.authentication_level,
      risk_score:
        typeof session.risk_score === 'number' ? session.risk_score : null,
    },
    logistics: {
      enabled: logistics.enabled,
      roles: logistics.roles,
      permissions: logistics.permissions,
      sensitive_permissions: logistics.sensitive_permissions,
      step_up_permissions: logistics.step_up_permissions,
      organizations: logistics.organizations,
      branches: logistics.branches,
      warehouses: logistics.warehouses,
      default_organization_id:
        typeof logistics.default_organization_id === 'string'
          ? logistics.default_organization_id
          : null,
      default_branch_id:
        typeof logistics.default_branch_id === 'string'
          ? logistics.default_branch_id
          : null,
      default_warehouse_id:
        typeof logistics.default_warehouse_id === 'string'
          ? logistics.default_warehouse_id
          : null,
    },
  }
}

export function parseLogisticsContextChangeResponse(
  value: unknown,
): LogisticsContextChangeResponse {
  if (!isRecord(value)) {
    throw new ApiRequestError('La respuesta de cambio de contexto no es válida.', {
      code: 'INVALID_RESPONSE',
    })
  }

  const context = value.context
  if (
    !isRecord(context) ||
    typeof context.enabled !== 'boolean' ||
    !isStringArray(context.roles) ||
    !isStringArray(context.permissions) ||
    !isStringArray(context.sensitive_permissions) ||
    !isStringArray(context.step_up_permissions) ||
    !isStringArray(context.organizations) ||
    !isStringArray(context.branches) ||
    !isStringArray(context.warehouses)
  ) {
    throw new ApiRequestError('El contexto devuelto no es válido.', {
      code: 'INVALID_RESPONSE',
    })
  }

  return {
    success: typeof value.success === 'boolean' ? value.success : true,
    message: typeof value.message === 'string' ? value.message : '',
    context: {
      enabled: context.enabled,
      roles: context.roles,
      permissions: context.permissions,
      sensitive_permissions: context.sensitive_permissions,
      step_up_permissions: context.step_up_permissions,
      organizations: context.organizations,
      branches: context.branches,
      warehouses: context.warehouses,
      default_organization_id:
        typeof context.default_organization_id === 'string'
          ? context.default_organization_id
          : null,
      default_branch_id:
        typeof context.default_branch_id === 'string'
          ? context.default_branch_id
          : null,
      default_warehouse_id:
        typeof context.default_warehouse_id === 'string'
          ? context.default_warehouse_id
          : null,
    },
  }
}

let inMemoryCache: LogisticsMeResponse | null = null
let pendingRequest: Promise<LogisticsMeResponse> | null = null

export function invalidateLogisticsMeCache(): void {
  inMemoryCache = null
  pendingRequest = null
}

export function getCachedLogisticsMe(): LogisticsMeResponse | null {
  return inMemoryCache
}

export async function getLogisticsMe(
  signal?: AbortSignal,
): Promise<LogisticsMeResponse> {
  if (inMemoryCache) return inMemoryCache
  if (pendingRequest) return pendingRequest

  pendingRequest = apiRequest<unknown>({
    path: '/logistics/me',
    method: 'GET',
    requiresCsrf: false,
    signal,
    timeout: LOGISTICS_BOOTSTRAP_TIMEOUT_MS,
  })
    .then((payload) => {
      const parsed = parseLogisticsMeResponse(payload)
      inMemoryCache = parsed
      return parsed
    })
    .finally(() => {
      pendingRequest = null
    })

  return pendingRequest
}

export async function refreshLogisticsMe(
  signal?: AbortSignal,
): Promise<LogisticsMeResponse> {
  invalidateLogisticsMeCache()
  return getLogisticsMe(signal)
}

export async function setLogisticsContext(
  request: LogisticsContextChangeRequest,
  signal?: AbortSignal,
): Promise<LogisticsContextChangeResponse> {
  const payload = await apiRequest<unknown>({
    path: '/logistics/me/context',
    method: 'POST',
    body: request,
    requiresCsrf: true,
    signal,
  })

  const parsed = parseLogisticsContextChangeResponse(payload)
  // Actualizar caché con el nuevo contexto
  if (inMemoryCache) {
    inMemoryCache = {
      ...inMemoryCache,
      logistics: parsed.context,
    }
  }
  return parsed
}
