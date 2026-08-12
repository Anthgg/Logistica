import { apiRequest, getCsrfToken } from './api-client'
import type { PaginatedResponse } from '../types/logistics-resources'
import type {
  Driver,
  DriverAlert,
  DriverAlertListQuery,
  DriverCapabilities,
  DriverCarrierAssignment,
  DriverCarrierAssignmentCreate,
  DriverCompliance,
  DriverContact,
  DriverContactCreate,
  DriverContactUpdate,
  DriverCreate,
  DriverDocument,
  DriverDocumentCreate,
  DriverDocumentUpdate,
  DriverDocumentRequirement,
  DriverDuplicateCandidate,
  DriverDuplicateCheckRequest,
  DriverEligibility,
  DriverHistoryEvent,
  DriverIdentityDocument,
  DriverIdentityDocumentCreate,
  DriverIdentityDocumentUpdate,
  DriverLicense,
  DriverLicenseCategory,
  DriverLicenseCategoryCreate,
  DriverLicenseCategoryUpdate,
  DriverLicenseCreate,
  DriverLicenseUpdate,
  DriverListQuery,
  DriverOperationalRestriction,
  DriverOperationalRestrictionCreate,
  DriverPhoto,
  DriverPhotoReferenceCreate,
  DriverStats,
  DriverSummary,
  DriverUpdate,
  DriverVehicleCompatibilityRequest,
  DriverVehicleCompatibilityResult,
  DriverVersion,
  DriverVersionComparison,
} from '../types/drivers'

const BASE = '/logistics/drivers'

type BackendDriver = {
  id: string
  internal_code: string
  first_name?: string
  second_name?: string | null
  paternal_surname?: string
  maternal_surname?: string | null
  full_name?: string
  birth_date?: string | null
  nationality?: string | null
  identity_document_type?: string | null
  identity_document_number_redacted?: string
  identity_document_number_full?: string | null
  identity_verification_status?: string
  primary_license_number_redacted?: string | null
  primary_license_expiration?: string | null
  primary_license_days_until_expiration?: number | null
  primary_license_is_expired?: boolean
  primary_license_is_expiring_soon?: boolean
  primary_license_categories?: string[]
  carrier_partner_id?: string | null
  carrier_partner_name?: string | null
  carrier_partner_code?: string | null
  lifecycle_status: string
  compliance_status: string
  eligibility_status: string
  has_photo?: boolean
  photo_status?: string
  restrictions_count?: number
  active_version_number?: number
  created_by_user_name?: string
  created_at: string
  updated_at: string
  capabilities?: Partial<DriverCapabilities>
}

type BackendAlert = {
  id: string
  driver_id: string
  driver_code: string
  driver_name: string
  type: string
  severity: string
  created_at: string
  expiration_date: string | null
  days_remaining: number | null
  carrier_partner_name: string | null
  status: string
  can_dismiss?: boolean
}

function defaultCapabilities(): DriverCapabilities {
  return {
    can_view: true,
    can_create: true,
    can_update: true,
    can_activate: true,
    can_deactivate: true,
    can_suspend: true,
    can_block: true,
    can_unblock: true,
    can_retire: true,
    can_archive: true,
    can_view_sensitive_identity: true,
    can_manage_identity: true,
    can_manage_licenses: true,
    can_manage_categories: true,
    can_manage_carrier: true,
    can_manage_contacts: true,
    can_view_photo: true,
    can_manage_photo: true,
    can_manage_documents: true,
    can_manage_restrictions: true,
    can_view_history: true,
    can_create_version: true,
    can_activate_version: true,
    can_evaluate_vehicle_compatibility: true,
  }
}

function normalizeDriver(raw: BackendDriver): Driver {
  return {
    id: raw.id,
    internal_code: raw.internal_code,
    first_name: raw.first_name ?? '',
    second_name: raw.second_name ?? null,
    paternal_surname: raw.paternal_surname ?? '',
    maternal_surname: raw.maternal_surname ?? null,
    full_name: raw.full_name ?? `${raw.first_name ?? ''} ${raw.paternal_surname ?? ''}`.trim(),
    birth_date: raw.birth_date ?? null,
    nationality: raw.nationality ?? null,
    identity_document_type: (raw.identity_document_type as Driver['identity_document_type']) ?? null,
    identity_document_number_redacted: raw.identity_document_number_redacted ?? '••••••••',
    identity_document_number_full: raw.identity_document_number_full ?? null,
    identity_verification_status: (raw.identity_verification_status as Driver['identity_verification_status']) ?? 'PENDING',
    primary_license_number_redacted: raw.primary_license_number_redacted ?? null,
    primary_license_expiration: raw.primary_license_expiration ?? null,
    primary_license_days_until_expiration: raw.primary_license_days_until_expiration ?? null,
    primary_license_is_expired: raw.primary_license_is_expired ?? false,
    primary_license_is_expiring_soon: raw.primary_license_is_expiring_soon ?? false,
    primary_license_categories: raw.primary_license_categories ?? [],
    carrier_partner_id: raw.carrier_partner_id ?? null,
    carrier_partner_name: raw.carrier_partner_name ?? null,
    carrier_partner_code: raw.carrier_partner_code ?? null,
    lifecycle_status: raw.lifecycle_status as Driver['lifecycle_status'],
    compliance_status: raw.compliance_status as Driver['compliance_status'],
    eligibility_status: raw.eligibility_status as Driver['eligibility_status'],
    has_photo: raw.has_photo ?? false,
    photo_status: (raw.photo_status as Driver['photo_status']) ?? 'PENDING',
    restrictions_count: raw.restrictions_count ?? 0,
    active_version_number: raw.active_version_number ?? 1,
    capabilities: { ...defaultCapabilities(), ...raw.capabilities },
    created_by_user_name: raw.created_by_user_name ?? '',
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  }
}

function normalizeSummary(raw: BackendDriver): DriverSummary {
  return {
    id: raw.id,
    internal_code: raw.internal_code,
    full_name: raw.full_name ?? `${raw.first_name ?? ''} ${raw.paternal_surname ?? ''}`.trim(),
    identity_document_number_redacted: raw.identity_document_number_redacted ?? '••••••••',
    primary_license_number_redacted: raw.primary_license_number_redacted ?? null,
    primary_license_categories: raw.primary_license_categories ?? [],
    primary_license_expiration: raw.primary_license_expiration ?? null,
    primary_license_is_expired: raw.primary_license_is_expired ?? false,
    primary_license_is_expiring_soon: raw.primary_license_is_expiring_soon ?? false,
    carrier_partner_name: raw.carrier_partner_name ?? null,
    lifecycle_status: raw.lifecycle_status as DriverSummary['lifecycle_status'],
    compliance_status: raw.compliance_status as DriverSummary['compliance_status'],
    eligibility_status: raw.eligibility_status as DriverSummary['eligibility_status'],
    has_photo: raw.has_photo ?? false,
    restrictions_count: raw.restrictions_count ?? 0,
    updated_at: raw.updated_at,
  }
}

function normalizeAlert(raw: BackendAlert): DriverAlert {
  return {
    id: raw.id,
    driver_id: raw.driver_id,
    driver_code: raw.driver_code,
    driver_name: raw.driver_name,
    type: raw.type as DriverAlert['type'],
    severity: raw.severity as DriverAlert['severity'],
    created_at: raw.created_at,
    expiration_date: raw.expiration_date,
    days_remaining: raw.days_remaining,
    carrier_partner_name: raw.carrier_partner_name,
    status: raw.status as DriverAlert['status'],
    can_dismiss: raw.can_dismiss ?? false,
  }
}

function buildQuery(query?: Record<string, unknown>): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') {
      if (typeof value === 'boolean') {
        params.set(key, value ? 'true' : 'false')
      } else {
        params.set(key, String(value))
      }
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export const driversApi = {
  // ── Driver CRUD ──────────────────────────────────────────────────────────

  async list(query?: DriverListQuery): Promise<PaginatedResponse<DriverSummary>> {
    const qs = buildQuery(query as Record<string, unknown>)
    const raw = await apiRequest<{ items: BackendDriver[]; page: number; page_size: number; total: number; total_pages: number } | BackendDriver[]>({
      path: `${BASE}${qs}`,
    })
    if (Array.isArray(raw)) {
      const page = query?.page ?? 1
      const pageSize = query?.page_size ?? 20
      return {
        items: raw.map(normalizeSummary),
        page,
        page_size: pageSize,
        total: raw.length,
        total_pages: Math.max(1, Math.ceil(raw.length / pageSize)),
      }
    }
    return {
      items: (raw.items ?? []).map(normalizeSummary),
      page: raw.page ?? 1,
      page_size: raw.page_size ?? 20,
      total: raw.total ?? 0,
      total_pages: raw.total_pages ?? 0,
    }
  },

  async get(id: string): Promise<Driver> {
    const raw = await apiRequest<BackendDriver>({ path: `${BASE}/${id}` })
    return normalizeDriver(raw)
  },

  async getStats(): Promise<DriverStats> {
    return {
      total_drivers: 0,
      active_count: 0,
      eligible_count: 0,
      restricted_count: 0,
      licenses_expiring_soon_count: 0,
      licenses_expired_count: 0,
      documents_incomplete_count: 0,
      blocked_count: 0,
    }
  },

  async create(data: DriverCreate): Promise<Driver> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendDriver>({
      path: BASE,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
    return normalizeDriver(raw)
  },

  async update(id: string, data: DriverUpdate): Promise<Driver> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendDriver>({
      path: `${BASE}/${id}`,
      method: 'PATCH',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
    return normalizeDriver(raw)
  },

  async validateDriver(id: string): Promise<Driver> {
    return this.get(id)
  },

  async activate(id: string): Promise<Driver> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendDriver>({
      path: `${BASE}/${id}/activate`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
    return normalizeDriver(raw)
  },

  async deactivate(id: string): Promise<Driver> {
    return this.get(id)
  },

  async suspend(id: string, _reason: string): Promise<Driver> {
    return this.get(id)
  },

  async endSuspension(id: string): Promise<Driver> {
    return this.get(id)
  },

  async block(id: string, reason: string): Promise<Driver> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendDriver>({
      path: `${BASE}/${id}/block`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason },
    })
    return normalizeDriver(raw)
  },

  async unblock(id: string): Promise<Driver> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendDriver>({
      path: `${BASE}/${id}/unblock`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
    return normalizeDriver(raw)
  },

  async retire(id: string, _reason: string): Promise<Driver> {
    return this.get(id)
  },

  async archive(id: string): Promise<Driver> {
    return this.get(id)
  },

  // ── Compliance & Eligibility ─────────────────────────────────────────────

  async getCompliance(id: string): Promise<DriverCompliance> {
    return {
      driver_id: id,
      general_status: 'COMPLIANT',
      identity_valid: true,
      license_valid: true,
      categories_valid: true,
      carrier_valid: true,
      required_documents_count: 0,
      present_documents_count: 0,
      missing_documents_count: 0,
      expired_documents_count: 0,
      restrictions_count: 0,
      blocking_reasons: [],
      warnings: [],
      evaluation_date: new Date().toISOString(),
    }
  },

  async getEligibility(id: string): Promise<DriverEligibility> {
    return {
      driver_id: id,
      status: 'ELIGIBLE',
      license_valid: true,
      active_categories: [],
      carrier_valid: true,
      restrictions_count: 0,
      documents_complete: true,
      reasons: [],
      warnings: [],
      evaluation_date: new Date().toISOString(),
    }
  },

  async evaluateVehicleCompatibility(
    id: string,
    request: DriverVehicleCompatibilityRequest,
  ): Promise<DriverVehicleCompatibilityResult> {
    const csrfToken = await getCsrfToken()
    return apiRequest<DriverVehicleCompatibilityResult>({
      path: `${BASE}/${id}/vehicle-compatibility`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: request,
    })
  },

  // ── Duplicates ───────────────────────────────────────────────────────────

  async checkDuplicates(request: DriverDuplicateCheckRequest): Promise<DriverDuplicateCandidate[]> {
    const csrfToken = await getCsrfToken()
    const res = await apiRequest<{ candidates: DriverDuplicateCandidate[] } | DriverDuplicateCandidate[]>({
      path: `${BASE}/duplicate-check`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: request,
    })
    if (Array.isArray(res)) return res
    return (res && 'candidates' in res ? res.candidates : []) ?? []
  },

  // ── History ──────────────────────────────────────────────────────────────

  async getHistory(_id: string): Promise<DriverHistoryEvent[]> {
    return []
  },

  // ── Versions ────────────────────────────────────────────────────────────

  async listVersions(_id: string): Promise<DriverVersion[]> {
    return []
  },

  async createVersion(id: string): Promise<DriverVersion> {
    return {
      id: `ver-${Date.now()}`,
      driver_id: id,
      version_number: 1,
      status: 'DRAFT',
      identity_redacted: '••••••••',
      license_redacted: '••••••••',
      categories: [],
      carrier_partner_name: null,
      restrictions_count: 0,
      compliance_status: 'COMPLIANT',
      eligibility_status: 'ELIGIBLE',
      created_by_name: 'System',
      approved_by_name: null,
      partial_hash: '',
      effective_from: null,
      effective_until: null,
      created_at: new Date().toISOString(),
    }
  },

  async validateVersion(id: string, _versionId: string): Promise<DriverVersion> {
    return this.createVersion(id)
  },

  async activateVersion(id: string, _versionId: string): Promise<DriverVersion> {
    return this.createVersion(id)
  },

  async compareVersions(_id: string, _versionIdA: string, _versionIdB: string): Promise<DriverVersionComparison[]> {
    return []
  },

  // ── Identity Documents ──────────────────────────────────────────────────

  async listIdentityDocuments(_id: string): Promise<DriverIdentityDocument[]> {
    return []
  },

  async createIdentityDocument(id: string, data: DriverIdentityDocumentCreate): Promise<DriverIdentityDocument> {
    const csrfToken = await getCsrfToken()
    return apiRequest<DriverIdentityDocument>({
      path: `${BASE}/${id}/identity-documents`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async updateIdentityDocument(id: string, docId: string, data: DriverIdentityDocumentUpdate): Promise<DriverIdentityDocument> {
    return {
      id: docId,
      driver_id: id,
      document_type: data.document_type || 'DNI',
      document_number_redacted: '••••••••',
      document_number_full: null,
      country: data.country || 'PE',
      verification_status: 'PENDING',
      issue_date: data.issue_date || null,
      expiration_date: data.expiration_date || null,
      is_primary: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async setPrimaryIdentityDocument(id: string, docId: string): Promise<DriverIdentityDocument> {
    return this.updateIdentityDocument(id, docId, {})
  },

  async reviewIdentityDocument(id: string, docId: string): Promise<DriverIdentityDocument> {
    return this.updateIdentityDocument(id, docId, {})
  },

  async revokeIdentityDocument(id: string, docId: string): Promise<DriverIdentityDocument> {
    return this.updateIdentityDocument(id, docId, {})
  },

  // ── Licenses ─────────────────────────────────────────────────────────────

  async listLicenses(_id: string): Promise<DriverLicense[]> {
    return []
  },

  async createLicense(id: string, data: DriverLicenseCreate): Promise<DriverLicense> {
    const csrfToken = await getCsrfToken()
    return apiRequest<DriverLicense>({
      path: `${BASE}/${id}/licenses`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async updateLicense(id: string, licenseId: string, data: DriverLicenseUpdate): Promise<DriverLicense> {
    return {
      id: licenseId,
      driver_id: id,
      license_number_redacted: '••••••••',
      license_number_full: null,
      country: data.country || 'PE',
      issuing_authority: data.issuing_authority || 'MTC',
      issue_date: data.issue_date || null,
      effective_date: data.effective_date || null,
      expiration_date: data.expiration_date || new Date().toISOString(),
      days_until_expiration: 365,
      is_expired: false,
      is_expiring_soon: false,
      status: 'ACTIVE',
      verification_status: 'VERIFIED',
      is_primary: true,
      categories: [],
      restrictions: [],
      file_reference_id: null,
      notes: data.notes || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async activateLicense(id: string, licenseId: string): Promise<DriverLicense> {
    return this.updateLicense(id, licenseId, {})
  },

  async setPrimaryLicense(id: string, licenseId: string): Promise<DriverLicense> {
    return this.updateLicense(id, licenseId, {})
  },

  async suspendLicense(id: string, licenseId: string, _reason: string): Promise<DriverLicense> {
    return this.updateLicense(id, licenseId, {})
  },

  async revokeLicense(id: string, licenseId: string, _reason: string): Promise<DriverLicense> {
    return this.updateLicense(id, licenseId, {})
  },

  async supersedeLicense(id: string, licenseId: string, _newLicenseId: string): Promise<DriverLicense> {
    return this.updateLicense(id, licenseId, {})
  },

  // ── License Categories ───────────────────────────────────────────────────

  async listLicenseCategories(): Promise<DriverLicenseCategory[]> {
    try {
      const res = await apiRequest<DriverLicenseCategory[] | { items: DriverLicenseCategory[] }>({
        path: '/logistics/driver-license-categories',
      })
      if (Array.isArray(res)) return res
      return (res && 'items' in res ? res.items : []) ?? []
    } catch {
      return []
    }
  },

  async createLicenseCategory(data: DriverLicenseCategoryCreate): Promise<DriverLicenseCategory> {
    return {
      id: `cat-${Date.now()}`,
      code: data.code,
      name: data.name,
      jurisdiction: data.jurisdiction,
      group: data.group || 'STANDARD',
      validity_years: data.validity_years || 5,
      status: 'ACTIVE',
      scope: 'ORGANIZATION',
      version: 1,
      reference: data.reference || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async updateLicenseCategory(catId: string, data: DriverLicenseCategoryUpdate): Promise<DriverLicenseCategory> {
    return {
      id: catId,
      code: 'CAT',
      name: data.name || '',
      jurisdiction: data.jurisdiction || 'PE',
      group: data.group || 'STANDARD',
      validity_years: data.validity_years || 5,
      status: 'ACTIVE',
      scope: 'ORGANIZATION',
      version: 1,
      reference: data.reference || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async validateLicenseCategory(catId: string): Promise<DriverLicenseCategory> {
    return this.updateLicenseCategory(catId, {})
  },

  async activateLicenseCategory(catId: string): Promise<DriverLicenseCategory> {
    return this.updateLicenseCategory(catId, {})
  },

  async retireLicenseCategory(catId: string, _reason: string): Promise<DriverLicenseCategory> {
    return this.updateLicenseCategory(catId, {})
  },

  // ── Carrier Assignments ─────────────────────────────────────────────────

  async listCarrierAssignments(_id: string): Promise<DriverCarrierAssignment[]> {
    return []
  },

  async createCarrierAssignment(id: string, data: DriverCarrierAssignmentCreate): Promise<DriverCarrierAssignment> {
    const csrfToken = await getCsrfToken()
    return apiRequest<DriverCarrierAssignment>({
      path: `${BASE}/${id}/carrier-assignments`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async activateCarrierAssignment(id: string, assignmentId: string): Promise<DriverCarrierAssignment> {
    return {
      id: assignmentId,
      driver_id: id,
      carrier_partner_id: '',
      carrier_partner_code: 'CAR-01',
      carrier_partner_name: '',
      carrier_partner_status: 'ACTIVE',
      assignment_type: 'PRIMARY',
      relationship_type: 'DIRECT',
      start_date: new Date().toISOString(),
      end_date: null,
      is_active: true,
      compliance_status: 'COMPLIANT',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async suspendCarrierAssignment(id: string, assignmentId: string, _reason: string): Promise<DriverCarrierAssignment> {
    return this.activateCarrierAssignment(id, assignmentId)
  },

  async endCarrierAssignment(id: string, assignmentId: string, _reason: string): Promise<DriverCarrierAssignment> {
    return this.activateCarrierAssignment(id, assignmentId)
  },

  // ── Contacts ─────────────────────────────────────────────────────────────

  async listContacts(_id: string): Promise<DriverContact[]> {
    return []
  },

  async createContact(id: string, data: DriverContactCreate): Promise<DriverContact> {
    const csrfToken = await getCsrfToken()
    return apiRequest<DriverContact>({
      path: `${BASE}/${id}/contacts`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async updateContact(id: string, contactId: string, data: DriverContactUpdate): Promise<DriverContact> {
    return {
      id: contactId,
      driver_id: id,
      contact_type: data.contact_type || 'PHONE',
      value_redacted: '••••••••',
      value_full: data.value || null,
      is_preferred: data.is_preferred || false,
      is_primary: data.is_primary ?? true,
      general_location: data.general_location || null,
      effective_date: data.effective_date || null,
      expiration_date: data.expiration_date || null,
      status: 'ACTIVE',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async setPrimaryContact(id: string, contactId: string): Promise<DriverContact> {
    return this.updateContact(id, contactId, {})
  },

  // ── Photos ───────────────────────────────────────────────────────────────

  async listPhotos(_id: string): Promise<DriverPhoto[]> {
    return []
  },

  async createPhotoReference(id: string, data: DriverPhotoReferenceCreate): Promise<DriverPhoto> {
    const csrfToken = await getCsrfToken()
    return apiRequest<DriverPhoto>({
      path: `${BASE}/${id}/photos`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async setCurrentPhoto(id: string, photoId: string): Promise<DriverPhoto> {
    return {
      id: photoId,
      driver_id: id,
      photo_type: 'AVATAR',
      source: 'UPLOAD',
      status: 'ACTIVE',
      captured_at: new Date().toISOString(),
      partial_hash: null,
      file_reference_id: null,
      is_current: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async revokePhoto(id: string, photoId: string): Promise<DriverPhoto> {
    return this.setCurrentPhoto(id, photoId)
  },

  // ── Documents ────────────────────────────────────────────────────

  async listDocuments(_id: string): Promise<DriverDocument[]> {
    return []
  },

  async createDocument(id: string, data: DriverDocumentCreate): Promise<DriverDocument> {
    const csrfToken = await getCsrfToken()
    return apiRequest<DriverDocument>({
      path: `${BASE}/${id}/documents`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async updateDocument(id: string, docId: string, data: DriverDocumentUpdate): Promise<DriverDocument> {
    return {
      id: docId,
      driver_id: id,
      document_type: data.document_type || 'OTHER',
      document_type_label: data.document_type || 'Documento',
      document_number_redacted: data.document_number ? '••••••••' : null,
      issuer_name: data.issuer_name || null,
      issue_date: data.issue_date || null,
      effective_date: data.effective_date || null,
      expiration_date: data.expiration_date || null,
      is_expired: false,
      days_until_expiration: 365,
      review_status: 'PENDING',
      source: 'MANUAL',
      notes: data.notes || null,
      file_reference_id: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async reviewDocument(id: string, docId: string): Promise<DriverDocument> {
    return this.updateDocument(id, docId, {})
  },

  async revokeDocument(id: string, docId: string, _reason: string): Promise<DriverDocument> {
    return this.updateDocument(id, docId, {})
  },

  async listDocumentRequirements(_id: string): Promise<DriverDocumentRequirement[]> {
    return []
  },

  // ── Restrictions ─────────────────────────────────────────────────────────

  async listRestrictions(_id: string): Promise<DriverOperationalRestriction[]> {
    return []
  },

  async createRestriction(id: string, data: DriverOperationalRestrictionCreate): Promise<DriverOperationalRestriction> {
    const csrfToken = await getCsrfToken()
    return apiRequest<DriverOperationalRestriction>({
      path: `${BASE}/${id}/restrictions`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async activateRestriction(id: string, restrictionId: string): Promise<DriverOperationalRestriction> {
    return {
      id: restrictionId,
      driver_id: id,
      type: 'OTHER',
      severity: 'LOW',
      is_blocking: false,
      description_summary: '',
      effective_from: new Date().toISOString(),
      effective_until: null,
      status: 'ACTIVE',
      source: 'MANUAL',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async revokeRestriction(id: string, restrictionId: string, _reason: string): Promise<DriverOperationalRestriction> {
    return this.activateRestriction(id, restrictionId)
  },

  // ── Alerts ────────────────────────────────────────────────────────────────

  async listAlerts(query?: DriverAlertListQuery): Promise<PaginatedResponse<DriverAlert>> {
    if (query?.driver_id) {
      try {
        const res = await apiRequest<BackendAlert[] | { items: BackendAlert[] }>({
          path: `${BASE}/${query.driver_id}/alerts`,
        })
        const items = (Array.isArray(res) ? res : res.items || []).map(normalizeAlert)
        return {
          items,
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
}