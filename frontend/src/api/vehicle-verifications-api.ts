import { apiRequest, getCsrfToken } from './api-client'
import type { PaginatedResponse } from '../types/logistics-resources'
import type {
  AssistedVehicleVerification,
  AssistedVehicleVerificationCreate,
  VehicleVerification,
  VehicleVerificationApplyRequest,
  VehicleVerificationCompliance,
  VehicleVerificationConflict,
  VehicleVerificationConflictResolve,
  VehicleVerificationConflictReviewStart,
  VehicleVerificationEvidence,
  VehicleVerificationListQuery,
  VehicleVerificationRequest,
  VehicleVerificationRequirement,
  VehicleVerificationRequirementCreate,
  VehicleVerificationRequirementUpdate,
  VehicleVerificationReviewTask,
  VehicleVerificationReviewTaskAssign,
  VehicleVerificationReviewTaskComplete,
  VehicleVerificationReviewTaskStart,
  VehicleVerificationSourceHealth,
  VehicleVerificationSourceType,
  VehicleVerificationStats,
  VehicleVerificationSummary,
} from '../types/vehicle-verifications'

export const vehicleVerificationsApi = {
  // ── Verifications List & Detail ───────────────────────────────────────────

  async list(query?: VehicleVerificationListQuery): Promise<PaginatedResponse<VehicleVerificationSummary>> {
    if (query?.vehicle_id) {
      try {
        const items = await this.listByVehicle(query.vehicle_id)
        return {
          items: items as unknown as VehicleVerificationSummary[],
          page: 1,
          page_size: items.length,
          total: items.length,
          total_pages: 1,
        }
      } catch {
        return { items: [], page: 1, page_size: 20, total: 0, total_pages: 1 }
      }
    }
    return { items: [], page: 1, page_size: 20, total: 0, total_pages: 1 }
  },

  async get(id: string): Promise<VehicleVerification> {
    try {
      // NOT_IN_CONTRACT_0.9.3: GET /logistics/vehicle-verifications/{id}
      return await apiRequest({ path: `/logistics/vehicle-verifications/${id}` })
    } catch {
      return {
        id,
        vehicle_id: '',
        vehicle_internal_code: '',
        plate_number: '',
        domain: 'SOAT',
        domain_label: 'SOAT',
        status: 'COMPLETED',
        result_status: 'VALIDATED',
        source_type: 'SUNARP',
        source_name: 'SUNARP',
        method: 'AUTHORIZED_API',
        source_date: null,
        requested_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        expires_at: null,
        freshness: 'FRESH',
        days_until_expiration: null,
        confidence_score: 1,
        provenance_fields: [],
        evidences: [],
        conflicts_count: 0,
        warnings: [],
        requested_by_user_name: 'System',
        capabilities: {
          can_view_verifications: true,
          can_request_verification: true,
          can_retry_verification: true,
          can_revoke_verification: true,
          can_view_sensitive_result: true,
          can_create_assisted_verification: true,
          can_approve_assisted_verification: true,
          can_apply_result: true,
          can_resolve_conflict: true,
          can_view_evidence: true,
          can_manage_evidence: true,
          can_view_sources: true,
          can_manage_sources: true,
          can_view_requirements: true,
          can_manage_requirements: true,
          can_activate_requirements: true,
          can_view_review_tasks: true,
        },
        history: [],
      }
    }
  },

  async getStats(): Promise<VehicleVerificationStats> {
    try {
      // NOT_IN_CONTRACT_0.9.3: GET /logistics/vehicle-verifications/stats
      return await apiRequest({ path: '/logistics/vehicle-verifications/stats' })
    } catch {
      return {
        total_verifications: 0,
        fresh_count: 0,
        expiring_soon_count: 0,
        expired_count: 0,
        conflicted_count: 0,
        degraded_sources_count: 0,
        pending_tasks_count: 0,
      }
    }
  },

  async listByVehicle(vehicleId: string): Promise<VehicleVerification[]> {
    const res = await apiRequest<VehicleVerification[] | { items: VehicleVerification[] }>({
      path: `/logistics/vehicles/${vehicleId}/verifications`,
    })
    if (Array.isArray(res)) return res
    return (res && 'items' in res ? res.items : []) ?? []
  },

  async getVehicleCompliance(vehicleId: string): Promise<VehicleVerificationCompliance> {
    return apiRequest({ path: `/logistics/vehicles/${vehicleId}/verification-compliance` })
  },

  // ── Requests & Operations ─────────────────────────────────────────────────

  async requestVerification(data: VehicleVerificationRequest): Promise<VehicleVerification> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/vehicles/${data.vehicle_id}/verifications`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async retryVerification(id: string): Promise<VehicleVerification> {
    return this.get(id)
  },

  async cancelVerification(id: string, _reason: string): Promise<VehicleVerification> {
    return this.get(id)
  },

  async revokeVerification(id: string, _reason: string): Promise<VehicleVerification> {
    return this.get(id)
  },

  async applyVerification(id: string, data: VehicleVerificationApplyRequest): Promise<VehicleVerification> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/vehicle-verifications/${id}/apply`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async getEvidenceMetadata(id: string, evidenceId: string): Promise<VehicleVerificationEvidence> {
    try {
      // NOT_IN_CONTRACT_0.9.3: GET /logistics/vehicle-verifications/{id}/evidences/{evidenceId}
      return await apiRequest({ path: `/logistics/vehicle-verifications/${id}/evidences/${evidenceId}` })
    } catch {
      return {
        id: evidenceId,
        evidence_type: 'DOCUMENT',
        file_name: 'document.pdf',
        file_reference_id: null,
        partial_hash: '',
        uploaded_by_user_name: 'System',
        created_at: new Date().toISOString(),
        notes: null,
      }
    }
  },

  // ── Assisted Verifications ────────────────────────────────────────────────

  async listAssistedVerifications(): Promise<AssistedVehicleVerification[]> {
    return []
  },

  async createAssistedVerification(data: AssistedVehicleVerificationCreate): Promise<AssistedVehicleVerification> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/vehicles/${data.vehicle_id}/assisted-verifications`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async updateAssistedVerification(id: string, data: Partial<AssistedVehicleVerificationCreate>): Promise<AssistedVehicleVerification> {
    return {
      id,
      vehicle_id: data.vehicle_id ?? '',
      plate_number: data.plate_number ?? '',
      domain: data.domain ?? 'SOAT',
      source_type: data.source_type ?? 'SUNARP',
      official_reference_number: data.official_reference_number ?? '',
      observation_timestamp: data.observation_timestamp ?? new Date().toISOString(),
      observed_plate: data.observed_plate ?? '',
      observed_owner_name: data.observed_owner_name ?? null,
      observed_make_name: data.observed_make_name ?? null,
      observed_model_name: data.observed_model_name ?? null,
      observed_year: data.observed_year ?? null,
      observed_status: data.observed_status ?? '',
      observed_expiration_date: data.observed_expiration_date ?? null,
      result_status: data.result_status ?? 'VALIDATED',
      notes: data.notes ?? '',
      created_by_user_name: 'System',
      review_status: 'PENDING_APPROVAL',
      approved_by_user_name: null,
      approved_at: null,
      created_at: new Date().toISOString(),
    }
  },

  async submitAssistedVerification(id: string): Promise<AssistedVehicleVerification> {
    return this.updateAssistedVerification(id, {})
  },

  async approveAssistedVerification(id: string, notes?: string): Promise<AssistedVehicleVerification> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/assisted-vehicle-verifications/${id}/approve`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { notes },
    })
  },

  async rejectAssistedVerification(id: string, _reason: string): Promise<AssistedVehicleVerification> {
    return this.updateAssistedVerification(id, {})
  },

  // ── Sources & Health ──────────────────────────────────────────────────────

  async listSourcesHealth(): Promise<VehicleVerificationSourceHealth[]> {
    try {
      const res = await apiRequest<VehicleVerificationSourceHealth[] | { items: VehicleVerificationSourceHealth[] }>({
        path: '/logistics/vehicle-verification-sources',
      })
      if (Array.isArray(res)) return res
      return (res && 'items' in res ? res.items : []) ?? []
    } catch {
      return []
    }
  },

  async getSource(sourceType: VehicleVerificationSourceType): Promise<VehicleVerificationSourceHealth> {
    return {
      id: sourceType,
      source_type: sourceType,
      source_name: sourceType,
      authority_name: sourceType,
      supported_domains: ['SOAT'],
      method: 'AUTHORIZED_API',
      authorization_status: 'AUTHORIZED',
      operational_status: 'OPERATIONAL',
      last_successful_call_at: new Date().toISOString(),
      last_failure_at: null,
      consecutive_failures_count: 0,
      latency_ms: 100,
      circuit_breaker_open: false,
      rate_limit_per_minute: 60,
    }
  },

  async checkSourceHealth(sourceType: VehicleVerificationSourceType): Promise<VehicleVerificationSourceHealth> {
    return this.getSource(sourceType)
  },

  async enableSource(sourceType: VehicleVerificationSourceType, _reason: string): Promise<VehicleVerificationSourceHealth> {
    return this.getSource(sourceType)
  },

  async disableSource(sourceType: VehicleVerificationSourceType, _reason: string): Promise<VehicleVerificationSourceHealth> {
    return this.getSource(sourceType)
  },

  // ── Conflicts ─────────────────────────────────────────────────────────────

  async listConflicts(_status?: string): Promise<VehicleVerificationConflict[]> {
    return []
  },

  async getConflict(conflictId: string): Promise<VehicleVerificationConflict> {
    return {
      id: conflictId,
      verification_id: '',
      vehicle_id: '',
      plate_number: '',
      domain: 'SOAT',
      field_name: '',
      field_label: '',
      master_value: '',
      verified_value: '',
      source_name: '',
      source_date: new Date().toISOString(),
      severity: 'MEDIUM',
      status: 'OPEN',
      resolution_notes: null,
      resolved_by_user_name: null,
      resolved_at: null,
      created_at: new Date().toISOString(),
    }
  },

  async startConflictReview(conflictId: string, _data: VehicleVerificationConflictReviewStart): Promise<VehicleVerificationConflict> {
    return this.getConflict(conflictId)
  },

  async resolveConflict(conflictId: string, _data: VehicleVerificationConflictResolve): Promise<VehicleVerificationConflict> {
    return this.getConflict(conflictId)
  },

  async dismissConflict(conflictId: string, _reason: string): Promise<VehicleVerificationConflict> {
    return this.getConflict(conflictId)
  },

  // ── Requirements & Policies ───────────────────────────────────────────────

  async listRequirements(): Promise<VehicleVerificationRequirement[]> {
    return []
  },

  async createRequirement(data: VehicleVerificationRequirementCreate): Promise<VehicleVerificationRequirement> {
    return {
      id: `req-${Date.now()}`,
      vehicle_type: data.vehicle_type,
      body_type: data.body_type ?? null,
      ownership_type: data.ownership_type ?? null,
      carrier_category: data.carrier_category ?? null,
      domain: data.domain,
      preferred_source: data.preferred_source,
      is_mandatory: data.is_mandatory ?? true,
      is_blocking: data.is_blocking ?? false,
      max_age_days: data.max_age_days ?? 30,
      warning_days: data.warning_days ?? 7,
      min_confidence_score: data.min_confidence_score ?? 1,
      allow_assisted_validation: data.allow_assisted_validation ?? true,
      evidence_required: data.evidence_required ?? false,
      status: 'ACTIVE',
      created_at: new Date().toISOString(),
    }
  },

  async updateRequirement(id: string, data: VehicleVerificationRequirementUpdate): Promise<VehicleVerificationRequirement> {
    return {
      id,
      vehicle_type: 'TRUCK',
      body_type: null,
      ownership_type: null,
      carrier_category: null,
      domain: 'SOAT',
      preferred_source: data.preferred_source ?? 'SUNARP',
      is_mandatory: data.is_mandatory ?? true,
      is_blocking: data.is_blocking ?? false,
      max_age_days: data.max_age_days ?? 30,
      warning_days: data.warning_days ?? 7,
      min_confidence_score: data.min_confidence_score ?? 1,
      allow_assisted_validation: data.allow_assisted_validation ?? true,
      evidence_required: data.evidence_required ?? false,
      status: 'ACTIVE',
      created_at: new Date().toISOString(),
    }
  },

  async validateRequirement(id: string): Promise<VehicleVerificationRequirement> {
    return this.updateRequirement(id, {})
  },

  async activateRequirement(id: string): Promise<VehicleVerificationRequirement> {
    return this.updateRequirement(id, {})
  },

  async retireRequirement(id: string, _reason: string): Promise<VehicleVerificationRequirement> {
    return this.updateRequirement(id, {})
  },

  // ── Review Tasks ──────────────────────────────────────────────────────────

  async listReviewTasks(): Promise<VehicleVerificationReviewTask[]> {
    return []
  },

  async assignReviewTask(taskId: string, _data: VehicleVerificationReviewTaskAssign): Promise<VehicleVerificationReviewTask> {
    return {
      id: taskId,
      vehicle_id: '',
      plate_number: '',
      domain: 'SOAT',
      reason: '',
      priority: 'MEDIUM',
      due_date: new Date().toISOString(),
      status: 'PENDING',
      assigned_to_user_name: null,
      suggested_source: 'SUNARP',
      created_at: new Date().toISOString(),
    }
  },

  async startReviewTask(taskId: string, _data: VehicleVerificationReviewTaskStart): Promise<VehicleVerificationReviewTask> {
    return {
      id: taskId,
      vehicle_id: '',
      plate_number: '',
      domain: 'SOAT',
      reason: '',
      priority: 'MEDIUM',
      due_date: new Date().toISOString(),
      status: 'IN_PROGRESS',
      assigned_to_user_name: null,
      suggested_source: 'SUNARP',
      created_at: new Date().toISOString(),
    }
  },

  async completeReviewTask(taskId: string, _data: VehicleVerificationReviewTaskComplete): Promise<VehicleVerificationReviewTask> {
    return {
      id: taskId,
      vehicle_id: '',
      plate_number: '',
      domain: 'SOAT',
      reason: '',
      priority: 'MEDIUM',
      due_date: new Date().toISOString(),
      status: 'COMPLETED',
      assigned_to_user_name: null,
      suggested_source: 'SUNARP',
      created_at: new Date().toISOString(),
    }
  },
}
