import { ApiRequestError } from './api'

export type LogisticsScopeType =
  | 'GLOBAL'
  | 'ORGANIZATION'
  | 'BRANCH'
  | 'WAREHOUSE'

export interface LogisticsRoleScope {
  role_code: string
  role_name: string
  scope_type: LogisticsScopeType
  organization_id: string | null
  branch_id: string | null
  warehouse_id: string | null
  expires_at: string | null
}

export interface LogisticsPermissionsContext {
  organization_id: string | null
  branch_id: string | null
  warehouse_id: string | null
}

export interface LogisticsPermissionsResponse {
  success: boolean
  catalog_version: string
  user_id: string
  permissions: string[]
  sensitive_permissions: string[]
  step_up_permissions: string[]
  roles: LogisticsRoleScope[]
}

export type LogisticsPermissionRiskLevel =
  | 'low'
  | 'medium'
  | 'high'
  | 'critical'

export interface LogisticsPermissionCatalogItem {
  id: string
  code: string
  resource: string
  action: string
  name: string
  description: string
  category: string
  risk_level: LogisticsPermissionRiskLevel
  is_sensitive: boolean
  requires_reason: boolean
  requires_step_up: boolean
  is_system: boolean
  status: string
  created_at: string
  updated_at: string
}

export interface AuthorizationCheckRequest {
  permission_code: string
  organization_id?: string | null
  branch_id?: string | null
  warehouse_id?: string | null
}

export interface AuthorizationCheckResponse {
  success: boolean
  allowed: boolean
  permission_code: string
  reason: string | null
}

export const LOGISTICS_PERMISSION_ERROR_CODES = new Set([
  'PERMISSION_DENIED',
  'PERMISSION_SCOPE_DENIED',
  'STEP_UP_REQUIRED',
  'SENSITIVE_ACTION_REASON_REQUIRED',
  'CROSS_ORGANIZATION_ACCESS_DENIED',
  'CROSS_BRANCH_ACCESS_DENIED',
  'CROSS_WAREHOUSE_ACCESS_DENIED',
])

export function isLogisticsPermissionError(
  error: unknown,
): error is ApiRequestError {
  return (
    error instanceof ApiRequestError &&
    (error.status === 403 ||
      LOGISTICS_PERMISSION_ERROR_CODES.has(error.code))
  )
}

export function isStepUpRequired(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    error.code === 'STEP_UP_REQUIRED'
  )
}

export function isReasonRequired(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    error.code === 'SENSITIVE_ACTION_REASON_REQUIRED'
  )
}

export interface StepUpRequiredDetails {
  code: 'STEP_UP_REQUIRED'
  permission: string | null
  challenge_id: string | null
  reason: string | null
}

export function extractStepUpDetails(
  error: unknown,
): StepUpRequiredDetails | null {
  if (!(error instanceof ApiRequestError) || !isStepUpRequired(error)) {
    return null
  }
  const details = error.details as Record<string, unknown> | undefined
  if (!details || typeof details !== 'object') return null
  return {
    code: 'STEP_UP_REQUIRED',
    permission:
      typeof details.permission === 'string' ? details.permission : null,
    challenge_id:
      typeof details.challenge_id === 'string'
        ? details.challenge_id
        : null,
    reason:
      typeof details.reason === 'string' ? details.reason : null,
  }
}