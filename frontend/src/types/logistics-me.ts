export interface LogisticsMeUser {
  id: string
  display_name: string
  email: string
  platform_role: string
  is_active: boolean
}

export interface LogisticsMeSession {
  id: string
  device_id: string | null
  expires_at: string
  authentication_level: string
  risk_score: number | null
}

export interface LogisticsMeContext {
  enabled: boolean
  roles: string[]
  permissions: string[]
  sensitive_permissions: string[]
  step_up_permissions: string[]
  organizations: string[]
  branches: string[]
  warehouses: string[]
  default_organization_id: string | null
  default_branch_id: string | null
  default_warehouse_id: string | null
}

export interface LogisticsMeResponse {
  success: boolean
  user: LogisticsMeUser
  session: LogisticsMeSession
  logistics: LogisticsMeContext
}

export interface LogisticsContextChangeRequest {
  organization_id: string | null
  branch_id: string | null
  warehouse_id: string | null
}

export interface LogisticsContextChangeResponse {
  success: boolean
  message: string
  context: LogisticsMeContext
}

export type LogisticsAccessStatus =
  | 'loading'
  | 'enabled'
  | 'disabled'
  | 'no_role'
  | 'no_scope'
  | 'session_expired'
  | 'error'

export const LOGISTICS_ME_ERROR_CODES = new Set([
  'AUTHENTICATION_REQUIRED',
  'SESSION_EXPIRED',
  'SESSION_REVOKED',
  'USER_INACTIVE',
  'LOGISTICS_ACCESS_DISABLED',
  'LOGISTICS_ROLE_REQUIRED',
  'LOGISTICS_SCOPE_REQUIRED',
  'LOGISTICS_CONTEXT_INVALID',
  'LOGISTICS_CONTEXT_DENIED',
  'CSRF_VALIDATION_FAILED',
  'PERMISSION_DENIED',
])

export function isLogisticsMeError(
  error: unknown,
): error is { code: string; status: number | null; message: string } {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    typeof (error as { code: unknown }).code === 'string'
  )
}

export function isSessionExpiredError(error: unknown): boolean {
  if (!isLogisticsMeError(error)) return false
  const code = (error as { code: string }).code
  return ['SESSION_EXPIRED', 'SESSION_REVOKED', 'AUTHENTICATION_REQUIRED'].includes(
    code,
  )
}

export function isLogisticsAccessDisabledError(error: unknown): boolean {
  if (!isLogisticsMeError(error)) return false
  const code = (error as { code: string }).code
  return ['LOGISTICS_ACCESS_DISABLED', 'LOGISTICS_ROLE_REQUIRED'].includes(code)
}

export function isLogisticsContextError(error: unknown): boolean {
  if (!isLogisticsMeError(error)) return false
  const code = (error as { code: string }).code
  return ['LOGISTICS_CONTEXT_INVALID', 'LOGISTICS_CONTEXT_DENIED'].includes(code)
}