import { apiRequest, getCsrfToken } from './api-client'
import type { PaginatedResponse } from '../types/logistics-resources'
import type {
  ApplyRucDataRequest,
  AssistedVerificationCreate,
  BusinessPartnerRucVerification,
  RucAssistedVerification,
  RucCapabilities,
  RucConfidenceLevel,
  RucDataset,
  RucDomicileCondition,
  RucFreshnessStatus,
  RucImportJob,
  RucLookupRequest,
  RucLookupResponse,
  RucSourceHealth,
  RucSourceType,
  RucTaxpayerStatus,
} from '../types/ruc-integration'

const BASE = '/logistics/ruc'

type JsonRecord = Record<string, unknown>

interface PartnerVerificationResult {
  verification_id: string
  ruc: string
  verification_result: string
  verified_legal_name: string | null
  confidence_level: RucConfidenceLevel
  status: string
}

const sessionImports: RucImportJob[] = []
const sessionAssistedVerifications: RucAssistedVerification[] = []
const sessionPartnerVerifications = new Map<string, BusinessPartnerRucVerification[]>()

function stringValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function numberValue(value: unknown, fallback = 0): number {
  if (typeof value === 'number') return value
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function nullableString(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null
}

function paginated<T>(items: T[]): PaginatedResponse<T> {
  return {
    items,
    page: 1,
    page_size: items.length,
    total: items.length,
    total_pages: items.length > 0 ? 1 : 0,
  }
}

function normalizeSource(value: unknown): RucSourceType {
  const source = stringValue(value).toUpperCase()
  if (source.includes('PROVIDER')) return 'AUTHORIZED_PROVIDER'
  if (source.includes('ASSISTED')) return 'ASSISTED_REVIEW'
  if (source.includes('ANNEX')) return 'ANNEX_PADRON'
  if (source.includes('PARTNER')) return 'PARTNER_DECLARED'
  if (source.includes('HERITAGE')) return 'HERITAGE'
  if (source.includes('SUNAT') || source.includes('PADRON') || source.includes('REGISTRY')) {
    return 'OFFICIAL_PADRON'
  }
  return 'UNKNOWN'
}

function normalizeTaxpayerStatus(value: unknown): RucTaxpayerStatus {
  const status = stringValue(value, 'DESCONOCIDO').toUpperCase()
  if (status === 'ACTIVE') return 'ACTIVO'
  if (
    status === 'ACTIVO' ||
    status === 'BAJA_PROVISIONAL' ||
    status === 'BAJA_DEFINITIVA' ||
    status === 'SUSPENSION_TEMPORAL' ||
    status === 'INHABILITADO'
  ) {
    return status
  }
  return 'DESCONOCIDO'
}

function normalizeDomicileCondition(value: unknown): RucDomicileCondition {
  const condition = stringValue(value, 'DESCONOCIDO').toUpperCase()
  if (
    condition === 'HABIDO' ||
    condition === 'NO_HABIDO' ||
    condition === 'NO_HALLADO' ||
    condition === 'PENDIENTE'
  ) {
    return condition
  }
  return 'DESCONOCIDO'
}

function normalizeFreshness(value: unknown, isStale = false): RucFreshnessStatus {
  const freshness = stringValue(value).toUpperCase()
  if (
    freshness === 'FRESH' ||
    freshness === 'AGING' ||
    freshness === 'STALE' ||
    freshness === 'CRITICAL'
  ) {
    return freshness
  }
  return isStale ? 'STALE' : 'FRESH'
}

function normalizeConfidence(value: unknown): RucConfidenceLevel {
  const confidence = stringValue(value, 'UNVERIFIED').toUpperCase()
  if (confidence === 'HIGH' || confidence === 'MEDIUM' || confidence === 'LOW') {
    return confidence
  }
  return 'UNVERIFIED'
}

function normalizeLookup(raw: JsonRecord): RucLookupResponse {
  const source = normalizeSource(raw.source)
  const sourceLabel = stringValue(raw.source_name, source === 'AUTHORIZED_PROVIDER' ? 'Proveedor autorizado' : 'Padrón SUNAT')
  const sourceDate = stringValue(raw.source_published_at, stringValue(raw.fetched_at, new Date().toISOString()))
  const lookupDate = stringValue(raw.lookup_at, new Date().toISOString())
  const taxpayerStatus = normalizeTaxpayerStatus(raw.taxpayer_status)
  const domicileCondition = normalizeDomicileCondition(raw.domicile_condition)
  const annexes = Array.isArray(raw.annex_addresses) ? raw.annex_addresses : []
  const provenanceRecord =
    raw.field_provenance && typeof raw.field_provenance === 'object'
      ? (raw.field_provenance as JsonRecord)
      : {}

  return {
    ruc: stringValue(raw.normalized_ruc, stringValue(raw.query_ruc)),
    legal_name: stringValue(raw.legal_name),
    trade_name: nullableString(raw.trade_name),
    taxpayer_status: taxpayerStatus,
    taxpayer_status_label: stringValue(raw.taxpayer_status_raw, taxpayerStatus),
    domicile_condition: domicileCondition,
    domicile_condition_label: stringValue(raw.domicile_condition_raw, domicileCondition),
    ubigeo: stringValue(raw.ubigeo_code),
    fiscal_address: nullableString(raw.fiscal_address),
    economic_activities: Array.isArray(raw.economic_activities)
      ? raw.economic_activities.filter((item): item is string => typeof item === 'string')
      : [],
    annex_addresses: annexes.map((item, index) => {
      const annex = (item ?? {}) as JsonRecord
      return {
        id: stringValue(annex.id, `${stringValue(raw.normalized_ruc)}-${index}`),
        address: stringValue(annex.address_normalized, stringValue(annex.address_raw)),
        ubigeo: stringValue(annex.ubigeo_code),
        department: nullableString(annex.department),
        province: nullableString(annex.province),
        district: nullableString(annex.district),
        source,
        source_label: sourceLabel,
        source_date: sourceDate,
        is_active: true,
      }
    }),
    source,
    source_label: sourceLabel,
    dataset_version: nullableString(raw.dataset_version_id),
    source_date: sourceDate,
    lookup_date: lookupDate,
    age_in_days: numberValue(raw.data_age_days),
    freshness_status: normalizeFreshness(raw.staleness_level, raw.is_stale === true),
    confidence_level: normalizeConfidence(raw.confidence_level),
    verification_status: 'VALIDATED',
    provider_used: nullableString(raw.provider_used),
    is_cached: stringValue(raw.cache_status).startsWith('HIT'),
    warnings: Array.isArray(raw.warnings)
      ? raw.warnings.filter((item): item is string => typeof item === 'string')
      : [],
    conflicts: [],
    provenance_by_field: Object.entries(provenanceRecord).map(([fieldName, value]) => {
      const field = (value ?? {}) as JsonRecord
      return {
        field_name: fieldName,
        field_label: stringValue(field.field_label, fieldName.replaceAll('_', ' ')),
        value: nullableString(field.value),
        source: normalizeSource(field.source ?? raw.source),
        source_label: stringValue(field.source_name, sourceLabel),
        source_date: stringValue(field.source_date, sourceDate),
        confidence: normalizeConfidence(field.confidence ?? raw.confidence_level),
        age_in_days: numberValue(field.age_days, numberValue(raw.data_age_days)),
        freshness_status: normalizeFreshness(field.staleness_level, field.is_stale === true),
        has_conflict: field.has_conflict === true,
      }
    }),
  }
}

function normalizeSourceHealth(raw: JsonRecord, index: number): RucSourceHealth {
  const sourceType = normalizeSource(raw.source_type)
  const status = stringValue(raw.status, 'OPERATIONAL').toUpperCase()
  return {
    source_id: stringValue(raw.id, stringValue(raw.code, `source-${index}`)),
    source_name: stringValue(raw.name, stringValue(raw.code, 'Fuente RUC')),
    source_type: sourceType,
    status:
      status === 'DEGRADED' ||
      status === 'DISABLED' ||
      status === 'FAILED' ||
      status === 'UNDER_REVIEW'
        ? status
        : 'OPERATIONAL',
    priority: numberValue(raw.priority, index + 1),
    last_successful_sync: nullableString(raw.last_successful_sync_at),
    last_failure: nullableString(raw.last_failure_at),
    consecutive_failures: numberValue(raw.consecutive_failures),
    active_dataset_version: nullableString(raw.active_dataset_version),
    age_in_days: numberValue(raw.age_in_days),
    freshness_status: normalizeFreshness(raw.freshness_status),
    capabilities: Array.isArray(raw.capabilities)
      ? raw.capabilities.filter((item): item is string => typeof item === 'string')
      : [],
  }
}

function normalizeDataset(raw: JsonRecord): RucDataset {
  const fetchedAt = stringValue(raw.fetched_at, new Date().toISOString())
  const activatedAt = stringValue(raw.activated_at, fetchedAt)
  const totalRows = numberValue(raw.total_rows)
  return {
    id: stringValue(raw.id),
    dataset_type: stringValue(raw.dataset_type, 'RUC_GENERAL'),
    version: stringValue(raw.version, stringValue(raw.id).slice(0, 8)),
    source: normalizeSource(raw.source ?? 'SUNAT_REDUCED_REGISTRY'),
    source_label: stringValue(raw.source_label, 'Padrón SUNAT'),
    published_date: fetchedAt,
    downloaded_date: fetchedAt,
    status: 'ACTIVE',
    statistics: {
      total_rows: totalRows,
      accepted_rows: totalRows,
      rejected_rows: 0,
      duplicate_rows: 0,
      new_records: 0,
      updated_records: 0,
      deleted_records: 0,
    },
    partial_hash: stringValue(raw.archive_hash),
    parser_name: stringValue(raw.parser_name, 'backend'),
    duration_seconds: 0,
    has_anomalies: false,
    anomaly_reasons: [],
    created_at: activatedAt,
  }
}

function normalizeImport(raw: JsonRecord): RucImportJob {
  const startedAt = stringValue(raw.started_at, stringValue(raw.created_at, new Date().toISOString()))
  return {
    id: stringValue(raw.id),
    dataset_id: nullableString(raw.dataset_id),
    dataset_type: stringValue(raw.dataset_type, 'RUC_GENERAL'),
    origin: stringValue(raw.trigger_type, 'MANUAL'),
    triggered_by_user_id: stringValue(raw.requested_by),
    triggered_by_user_name: stringValue(raw.requested_by, 'Usuario actual'),
    status: stringValue(raw.status, 'QUEUED') as RucImportJob['status'],
    stage: stringValue(raw.current_stage, 'INIT'),
    progress_pct: numberValue(raw.progress_percent),
    processed_rows: numberValue(raw.processed_rows),
    total_rows: numberValue(raw.total_rows, numberValue(raw.accepted_rows) + numberValue(raw.rejected_rows)),
    started_at: startedAt,
    ended_at: nullableString(raw.completed_at),
    duration_seconds: null,
    error_message: nullableString(raw.error_summary),
  }
}

function normalizeAssisted(raw: JsonRecord): RucAssistedVerification {
  const approvedAt = nullableString(raw.approved_at)
  return {
    id: stringValue(raw.id),
    ruc: stringValue(raw.ruc),
    partner_id: nullableString(raw.business_partner_id),
    partner_name: null,
    reason: stringValue(raw.verification_reason),
    source_type: normalizeSource(raw.source_type ?? 'ASSISTED_OFFICIAL_REVIEW'),
    reference_number: nullableString(raw.source_reference),
    reviewed_at: stringValue(raw.reviewed_at, stringValue(raw.created_at, new Date().toISOString())),
    observed_legal_name: stringValue(raw.observed_legal_name),
    observed_status: normalizeTaxpayerStatus(raw.observed_status),
    observed_condition: normalizeDomicileCondition(raw.observed_condition),
    observed_ubigeo: stringValue(raw.observed_ubigeo),
    result: approvedAt ? 'APPROVED' : 'OBSERVED',
    observations: stringValue(raw.observations),
    created_by_user_id: stringValue(raw.reviewed_by),
    created_by_user_name: stringValue(raw.reviewed_by, 'Usuario actual'),
    approved_by_user_id: nullableString(raw.approved_by),
    approved_by_user_name: nullableString(raw.approved_by),
    approved_at: approvedAt,
    status: approvedAt ? 'APPROVED' : 'PENDING_APPROVAL',
    created_at: stringValue(raw.created_at, new Date().toISOString()),
  }
}

export const rucIntegrationApi = {
  async lookupRuc(req: RucLookupRequest): Promise<RucLookupResponse> {
    const params = new URLSearchParams()
    if (req.include_annexes) params.set('include_annexes', 'true')
    if (req.use_authorized_provider) params.set('allow_provider', 'true')
    const query = params.toString()
    const raw = await apiRequest<JsonRecord>({
      path: `${BASE}/${encodeURIComponent(req.ruc)}${query ? `?${query}` : ''}`,
    })
    return normalizeLookup(raw)
  },

  async listSources(): Promise<RucSourceHealth[]> {
    const raw = await apiRequest<JsonRecord[]>({ path: `${BASE}/sources/health` })
    return raw.map(normalizeSourceHealth)
  },

  async getCapabilities(): Promise<RucCapabilities> {
    return {
      can_lookup_RUC: true,
      can_lookup_enriched_RUC: false,
      can_view_annexes: true,
      can_create_assisted_verification: true,
      can_approve_assisted_verification: true,
      can_apply_to_partner: true,
      can_view_sources: true,
      can_view_datasets: true,
      can_start_import: true,
      can_activate_dataset: true,
      can_rollback_dataset: false,
      can_use_authorized_provider: true,
      can_view_technical_metrics: false,
    }
  },

  async listDatasets(): Promise<PaginatedResponse<RucDataset>> {
    const raw = await apiRequest<JsonRecord[]>({ path: `${BASE}/datasets/current` })
    return paginated(raw.map(normalizeDataset))
  },

  async activateDataset(id: string, _reason?: string): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `${BASE}/datasets/${id}/activate`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
  },

  async startImport(datasetType: string, _reason: string): Promise<RucImportJob> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<JsonRecord>({
      path: `${BASE}/imports`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { dataset_type: datasetType },
    })
    const job = normalizeImport(raw)
    sessionImports.unshift(job)
    return job
  },

  async listImports(): Promise<PaginatedResponse<RucImportJob>> {
    return paginated(sessionImports)
  },

  async getImport(id: string): Promise<RucImportJob> {
    const raw = await apiRequest<JsonRecord>({ path: `${BASE}/imports/${id}` })
    const job = normalizeImport(raw)
    const existingIndex = sessionImports.findIndex((item) => item.id === job.id)
    if (existingIndex >= 0) sessionImports[existingIndex] = job
    else sessionImports.unshift(job)
    return job
  },

  async createAssistedVerification(data: AssistedVerificationCreate): Promise<RucAssistedVerification> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<JsonRecord>({
      path: `${BASE}/assisted-verifications`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        ruc: data.ruc,
        verification_reason: data.reason,
        source_reference: data.reference_number || data.source_type,
        business_partner_id: data.partner_id,
        observed_legal_name: data.observed_legal_name,
        observed_status: data.observed_status,
        observed_condition: data.observed_condition,
        observed_ubigeo: data.observed_ubigeo,
        observations: data.observations,
      },
    })
    const verification = normalizeAssisted(raw)
    sessionAssistedVerifications.unshift(verification)
    return verification
  },

  async listAssistedVerifications(): Promise<PaginatedResponse<RucAssistedVerification>> {
    return paginated(sessionAssistedVerifications)
  },

  async approveAssistedVerification(id: string): Promise<RucAssistedVerification> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<JsonRecord>({
      path: `${BASE}/assisted-verifications/${id}/approve`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
    const verification = normalizeAssisted(raw)
    const existingIndex = sessionAssistedVerifications.findIndex((item) => item.id === id)
    if (existingIndex >= 0) sessionAssistedVerifications[existingIndex] = verification
    return verification
  },

  async listPartnerVerifications(partnerId: string): Promise<BusinessPartnerRucVerification[]> {
    return sessionPartnerVerifications.get(partnerId) ?? []
  },

  async verifyPartnerRuc(partnerId: string, allowProvider = false): Promise<PartnerVerificationResult> {
    const csrfToken = await getCsrfToken()
    const params = new URLSearchParams()
    if (allowProvider) params.set('allow_provider', 'true')
    const query = params.toString()
    const raw = await apiRequest<JsonRecord>({
      path: `${BASE}/business-partners/${partnerId}/verify-ruc${query ? `?${query}` : ''}`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
    const result: PartnerVerificationResult = {
      verification_id: stringValue(raw.verification_id),
      ruc: stringValue(raw.ruc),
      verification_result: stringValue(raw.verification_result, 'VERIFIED'),
      verified_legal_name: nullableString(raw.verified_legal_name),
      confidence_level: normalizeConfidence(raw.confidence_level),
      status: stringValue(raw.status, 'CURRENT'),
    }
    const historyItem: BusinessPartnerRucVerification = {
      id: result.verification_id,
      partner_id: partnerId,
      ruc: result.ruc,
      verification_date: new Date().toISOString(),
      source: allowProvider ? 'AUTHORIZED_PROVIDER' : 'OFFICIAL_PADRON',
      source_label: allowProvider ? 'Proveedor autorizado' : 'Padrón SUNAT',
      dataset_version: null,
      confidence_level: result.confidence_level,
      taxpayer_status: 'DESCONOCIDO',
      domicile_condition: 'DESCONOCIDO',
      age_in_days: 0,
      freshness_status: 'FRESH',
      verification_status: 'VALIDATED',
      applied_fields: [],
      conflicts_count: 0,
      created_by_name: 'Usuario actual',
    }
    sessionPartnerVerifications.set(partnerId, [
      historyItem,
      ...(sessionPartnerVerifications.get(partnerId) ?? []).filter((item) => item.id !== historyItem.id),
    ])
    return result
  },

  async applyRucDataToPartner(partnerId: string, req: ApplyRucDataRequest): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `${BASE}/business-partners/${partnerId}/apply-ruc-data`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: req,
    })
  },
}
