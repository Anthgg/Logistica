import { apiRequest } from '../../../api/api-client'
import { ApiRequestError } from '../../../types/api'
import type {
  AdminEntitySummary,
  AdminEvaluationDetail,
  AdminEvaluationPage,
  AdminEvaluationSummary,
  AuthenticationLevel,
  ComponentStatus,
  ContinuousAuthComponentSummary,
  ContinuousAuthEvaluationRequest,
  ContinuousAuthEvaluationResponse,
  ContinuousAuthStatus,
  EvaluationListQuery,
  ModelStatus,
  RecommendedAction,
  ReverificationRequest,
  ReverificationResponse,
  RiskLevel,
} from '../types/continuous-auth'

const riskLevels = new Set<RiskLevel>([
  'low',
  'medium',
  'high',
  'critical',
  'unknown',
])
const authenticationLevels = new Set<AuthenticationLevel>([
  'traditional',
  'continuously_verified',
  'verification_required',
  'restricted',
  'terminated',
])
const actions = new Set<RecommendedAction>([
  'maintain_session',
  'increase_monitoring',
  'request_reverification',
  'restrict_sensitive_operations',
  'terminate_session',
  'none',
])
const componentStatuses = new Set<ComponentStatus>([
  'available',
  'unavailable',
  'pending',
  'failed',
  'degraded',
])

function invalidResponse(): never {
  throw new ApiRequestError(
    'El servicio de verificación devolvió una respuesta inesperada.',
    { code: 'INVALID_RESPONSE' },
  )
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function requiredString(
  value: unknown,
  options: { allowEmpty?: boolean } = {},
): string {
  if (
    typeof value !== 'string' ||
    (!options.allowEmpty && value.trim().length === 0)
  ) {
    return invalidResponse()
  }

  return value
}

function nullableString(value: unknown): string | null {
  return value === null || value === undefined ? null : requiredString(value)
}

function sanitizedTechnicalMessage(value: unknown): string | null {
  const message = nullableString(value)
  if (!message) {
    return null
  }

  const exposesInternalDetail =
    /tensorflow|onnx|sqlalchemy|postgres|traceback|\.py\b|[a-z]:\\|\/(?:app|models|srv|home)\//i.test(
      message,
    )

  return exposesInternalDetail
    ? 'Un componente no está disponible temporalmente.'
    : message.slice(0, 240)
}

function requiredBoolean(value: unknown): boolean {
  return typeof value === 'boolean' ? value : invalidResponse()
}

function requiredNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value)
    ? value
    : invalidResponse()
}

function nullableNumber(value: unknown): number | null {
  return value === null || value === undefined
    ? null
    : requiredNumber(value)
}

function readRiskLevel(value: unknown): RiskLevel {
  if (value === null || value === undefined) {
    return 'unknown'
  }

  return typeof value === 'string' && riskLevels.has(value as RiskLevel)
    ? (value as RiskLevel)
    : invalidResponse()
}

function readAuthenticationLevel(value: unknown): AuthenticationLevel {
  return (
    typeof value === 'string' &&
    authenticationLevels.has(value as AuthenticationLevel)
  )
    ? (value as AuthenticationLevel)
    : invalidResponse()
}

function readAction(value: unknown): RecommendedAction {
  if (value === null || value === undefined) {
    return 'none'
  }

  return typeof value === 'string' && actions.has(value as RecommendedAction)
    ? (value as RecommendedAction)
    : invalidResponse()
}

function readComponentStatus(value: unknown): ComponentStatus {
  return (
    typeof value === 'string' &&
    componentStatuses.has(value as ComponentStatus)
  )
    ? (value as ComponentStatus)
    : invalidResponse()
}

function componentStatus(
  value: unknown,
  available: boolean,
): ComponentStatus {
  if (
    typeof value === 'string' &&
    componentStatuses.has(value as ComponentStatus)
  ) {
    return readComponentStatus(value)
  }

  return available ? 'available' : 'unavailable'
}

function componentSummary(
  name: string,
  available: boolean,
  rawStatus?: unknown,
): ContinuousAuthComponentSummary {
  const normalizedStatus = componentStatus(rawStatus, available)
  const reason =
    typeof rawStatus === 'string' &&
    !componentStatuses.has(rawStatus as ComponentStatus)
      ? rawStatus
      : null

  return {
    name,
    available,
    status: normalizedStatus,
    last_evaluated_at: null,
    reason,
  }
}

function readAvailabilityComponents(
  value: unknown,
): ContinuousAuthComponentSummary[] {
  if (!isRecord(value)) {
    return invalidResponse()
  }

  return Object.entries(value).map(([name, available]) =>
    componentSummary(name, requiredBoolean(available)),
  )
}

function readEvaluationComponents(
  value: unknown,
): ContinuousAuthComponentSummary[] {
  if (!isRecord(value)) {
    return invalidResponse()
  }

  return Object.entries(value).map(([name, component]) => {
    if (!isRecord(component)) {
      return invalidResponse()
    }

    return componentSummary(
      name,
      requiredBoolean(component.available),
      component.status,
    )
  })
}

function readStringRecord(value: unknown): Record<string, string> {
  if (!isRecord(value)) {
    return invalidResponse()
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, entry]) => [
      key,
      requiredString(entry, { allowEmpty: true }),
    ]),
  )
}

function readLatency(
  value: unknown,
): number | Record<string, number> {
  if (typeof value === 'number') {
    return requiredNumber(value)
  }

  if (!isRecord(value)) {
    return invalidResponse()
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, entry]) => [
      key,
      requiredNumber(entry),
    ]),
  )
}

function readEntity(
  value: unknown,
  fallbackId?: string,
): AdminEntitySummary {
  if (typeof value === 'string') {
    return { id: value, label: null }
  }

  if (!isRecord(value)) {
    if (fallbackId) {
      return { id: fallbackId, label: null }
    }
    return invalidResponse()
  }

  const id = requiredString(value.id ?? fallbackId)
  const candidateLabel =
    value.full_name ??
    value.email ??
    value.participant_code ??
    value.device_name ??
    null

  return {
    id,
    label: nullableString(candidateLabel),
  }
}

function parseStatus(payload: unknown): ContinuousAuthStatus {
  if (!isRecord(payload)) {
    return invalidResponse()
  }

  return {
    enabled: requiredBoolean(payload.enabled),
    continuous_auth_status: requiredString(
      payload.continuous_auth_status,
    ),
    risk_level: readRiskLevel(payload.risk_level),
    authentication_level: readAuthenticationLevel(
      payload.authentication_level,
    ),
    last_evaluation_at: nullableString(payload.last_evaluation_at),
    recommended_action: readAction(payload.recommended_action),
    applied_action: readAction(payload.applied_action),
    components_available: readAvailabilityComponents(
      payload.components_available,
    ),
    next_evaluation_after: nullableString(payload.next_evaluation_after),
    degraded: false,
    degraded_reason: null,
  }
}

function parseEvaluation(
  payload: unknown,
): ContinuousAuthEvaluationResponse {
  if (!isRecord(payload) || !isRecord(payload.evaluation)) {
    return invalidResponse()
  }

  const evaluation = payload.evaluation

  return {
    id: requiredString(evaluation.id),
    risk_score: requiredNumber(evaluation.risk_score),
    risk_level: readRiskLevel(evaluation.risk_level),
    authentication_level: readAuthenticationLevel(
      evaluation.authentication_level,
    ),
    recommended_action: readAction(evaluation.recommended_action),
    applied_action: readAction(evaluation.applied_action),
    evaluated_at: requiredString(evaluation.evaluated_at),
    components: readEvaluationComponents(evaluation.components),
  }
}

function parseReverification(payload: unknown): ReverificationResponse {
  if (!isRecord(payload)) {
    return invalidResponse()
  }

  return {
    success: requiredBoolean(payload.success),
    authentication_level: readAuthenticationLevel(
      payload.authentication_level,
    ),
    continuous_auth_status: requiredString(
      payload.continuous_auth_status,
    ),
    reverified_at: requiredString(payload.reverified_at),
  }
}

function parseEvaluationSummary(
  payload: unknown,
): AdminEvaluationSummary {
  if (!isRecord(payload)) {
    return invalidResponse()
  }

  return {
    id: requiredString(payload.id),
    user_id: requiredString(payload.user_id),
    session_id: requiredString(payload.session_id),
    participant_id: nullableString(payload.participant_id),
    risk_level: readRiskLevel(payload.risk_level),
    authentication_level: readAuthenticationLevel(
      payload.authentication_level,
    ),
    recommended_action: readAction(payload.recommended_action),
    applied_action: readAction(payload.applied_action),
    latency_ms: requiredNumber(payload.latency_ms),
    evaluated_at: requiredString(payload.evaluated_at),
  }
}

function parseEvaluationPage(payload: unknown): AdminEvaluationPage {
  if (!isRecord(payload) || !Array.isArray(payload.items)) {
    return invalidResponse()
  }

  return {
    items: payload.items.map(parseEvaluationSummary),
    page: requiredNumber(payload.page),
    page_size: requiredNumber(payload.page_size),
    total: requiredNumber(payload.total),
    total_pages: requiredNumber(payload.total_pages),
  }
}

function parseEvaluationDetail(
  payload: unknown,
): AdminEvaluationDetail {
  if (!isRecord(payload)) {
    return invalidResponse()
  }

  return {
    id: requiredString(payload.id),
    user: readEntity(payload.user_id),
    session: readEntity(payload.session_id),
    participant:
      payload.participant_id === null ||
      payload.participant_id === undefined
        ? null
        : readEntity(payload.participant_id),
    component_scores: {
      ...(requiredBoolean(payload.facial_available)
        ? { facial: nullableNumber(payload.facial_score) }
        : {}),
      ...(requiredBoolean(payload.pad_available)
        ? { pad: nullableNumber(payload.pad_score) }
        : {}),
      ...(requiredBoolean(payload.behavioral_available)
        ? { behavioral: nullableNumber(payload.behavioral_score) }
        : {}),
    },
    component_risks: {
      ...(requiredBoolean(payload.facial_available)
        ? { facial: nullableNumber(payload.facial_risk) }
        : {}),
      ...(requiredBoolean(payload.pad_available)
        ? { pad: nullableNumber(payload.pad_risk) }
        : {}),
      ...(requiredBoolean(payload.behavioral_available)
        ? { behavioral: nullableNumber(payload.behavioral_risk) }
        : {}),
    },
    combined_risk: nullableNumber(payload.combined_risk),
    risk_level: readRiskLevel(payload.risk_level),
    authentication_level: readAuthenticationLevel(
      payload.authentication_level,
    ),
    recommended_action: readAction(payload.recommended_action),
    applied_action: readAction(payload.applied_action),
    model_versions: readStringRecord(payload.model_versions),
    latency:
      isRecord(payload.latency_breakdown) &&
      Object.keys(payload.latency_breakdown).length > 0
        ? readLatency(payload.latency_breakdown)
        : requiredNumber(payload.latency_ms),
    evaluated_at: requiredString(payload.evaluated_at),
  }
}

function parseModelStatus(payload: unknown): ModelStatus {
  if (!isRecord(payload) || !isRecord(payload.models)) {
    return invalidResponse()
  }

  const models = payload.models
  if (
    !isRecord(models.facial) ||
    !isRecord(models.pad) ||
    !Array.isArray(models.behavioral_versions) ||
    !Array.isArray(models.errors)
  ) {
    return invalidResponse()
  }

  const facialVersion = nullableString(models.facial.version)
  const padVersion = nullableString(models.pad.version)
  const behavioralVersions = models.behavioral_versions.map((entry) =>
    requiredString(entry),
  )

  return {
    overall_status: requiredString(models.global_status),
    facial_loaded: requiredBoolean(models.facial.loaded),
    pad_loaded: requiredBoolean(models.pad.loaded),
    behavioral_available_count: requiredNumber(
      models.behavioral_available,
    ),
    behavioral_loaded_count: requiredNumber(
      models.behavioral_loaded,
    ),
    versions: {
      facial: facialVersion ?? 'No disponible',
      pad: padVersion ?? 'No disponible',
      behavioral:
        behavioralVersions.join(', ') || 'No disponible',
    },
    device: requiredString(models.device),
    loaded_at: nullableString(models.loaded_at),
    checksums_valid:
      requiredBoolean(models.registry_checksum_valid) &&
      requiredBoolean(models.facial.checksum_valid) &&
      requiredBoolean(models.pad.checksum_valid),
    fusion_loaded: requiredBoolean(models.fusion_loaded),
    normalization_loaded: requiredBoolean(models.normalization_loaded),
    errors: models.errors.map(
      (entry) =>
        sanitizedTechnicalMessage(entry) ??
        'Un componente no está disponible temporalmente.',
    ),
  }
}

function toQueryString(query: EvaluationListQuery): string {
  const parameters = new URLSearchParams()

  Object.entries({
    user_id: query.user_id,
    session_id: query.session_id,
    participant_id: query.participant_id,
    risk_level: query.risk_level,
    authentication_level: query.authentication_level,
    date_from: query.date_from,
    date_to: query.date_to,
    page: query.page,
    page_size: query.page_size,
  }).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      parameters.set(key, String(value))
    }
  })

  const value = parameters.toString()
  return value ? `?${value}` : ''
}

export async function getContinuousAuthStatus(
  signal?: AbortSignal,
): Promise<ContinuousAuthStatus> {
  const payload = await apiRequest<unknown>({
    path: '/continuous-auth/status',
    signal,
  })
  return parseStatus(payload)
}

export async function requestContinuousAuthEvaluation(
  request: ContinuousAuthEvaluationRequest,
  signal?: AbortSignal,
): Promise<ContinuousAuthEvaluationResponse> {
  const payload = await apiRequest<unknown>({
    path: '/continuous-auth/evaluate',
    method: 'POST',
    body: request,
    signal,
  })
  return parseEvaluation(payload)
}

export async function reverifyContinuousAuth(
  request: ReverificationRequest,
  signal?: AbortSignal,
): Promise<ReverificationResponse> {
  const payload = await apiRequest<unknown>({
    path: '/continuous-auth/reverify',
    method: 'POST',
    body: request,
    signal,
  })
  return parseReverification(payload)
}

export async function getEvaluations(
  query: EvaluationListQuery,
  signal?: AbortSignal,
): Promise<AdminEvaluationPage> {
  const payload = await apiRequest<unknown>({
    path: `/continuous-auth/evaluations${toQueryString(query)}`,
    signal,
  })
  return parseEvaluationPage(payload)
}

export async function getEvaluationDetail(
  evaluationId: string,
  signal?: AbortSignal,
): Promise<AdminEvaluationDetail> {
  const payload = await apiRequest<unknown>({
    path: `/continuous-auth/evaluations/${encodeURIComponent(evaluationId)}`,
    signal,
  })
  return parseEvaluationDetail(payload)
}

export async function getModelStatus(
  signal?: AbortSignal,
): Promise<ModelStatus> {
  const payload = await apiRequest<unknown>({
    path: '/models/status',
    signal,
  })
  return parseModelStatus(payload)
}
