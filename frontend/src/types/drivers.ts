// ─── Driver Master – TypeScript strict types (Phase 029) ──────────────────────
// Driver ≠ User. Driver ≠ Employee. No accounts, no payroll, no attendance.

import type { PaginatedResponse } from './logistics-resources'

// ─── Lifecycle ───────────────────────────────────────────────────────────────

export type DriverLifecycleStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'INACTIVE'
  | 'SUSPENDED'
  | 'BLOCKED'
  | 'RETIRED'
  | 'ARCHIVED'

export type DriverComplianceStatus =
  | 'UNEVALUATED'
  | 'COMPLIANT'
  | 'PARTIAL'
  | 'NON_COMPLIANT'
  | 'DOCUMENTS_EXPIRED'
  | 'LICENSE_EXPIRED'
  | 'LICENSE_SUSPENDED'
  | 'UNDER_REVIEW'
  | 'CONFLICT'

export type DriverEligibilityStatus =
  | 'UNEVALUATED'
  | 'ELIGIBLE'
  | 'INELIGIBLE'
  | 'RESTRICTED'
  | 'LICENSE_EXPIRED'
  | 'DOCUMENTS_INCOMPLETE'
  | 'CARRIER_INACTIVE'
  | 'BLOCKED'
  | 'UNDER_REVIEW'

// ─── Identity ─────────────────────────────────────────────────────────────────

export type DriverIdentityDocumentType =
  | 'DNI'
  | 'CE'
  | 'PASSPORT'
  | 'FOREIGN_ID'
  | 'OTHER'

export type DriverIdentityVerificationStatus =
  | 'PENDING'
  | 'VERIFIED'
  | 'REJECTED'
  | 'EXPIRED'
  | 'REVOKED'
  | 'ARCHIVED'

export interface DriverIdentityDocument {
  id: string
  driver_id: string
  document_type: DriverIdentityDocumentType
  document_number_redacted: string
  document_number_full: string | null
  country: string
  verification_status: DriverIdentityVerificationStatus
  issue_date: string | null
  expiration_date: string | null
  is_primary: boolean
  created_at: string
  updated_at: string
}

export interface DriverIdentityDocumentCreate {
  document_type: DriverIdentityDocumentType
  document_number: string
  country?: string
  issue_date?: string
  expiration_date?: string
  is_primary?: boolean
}

export interface DriverIdentityDocumentUpdate {
  document_type?: DriverIdentityDocumentType
  document_number?: string
  country?: string
  issue_date?: string
  expiration_date?: string
}

// ─── Licenses ────────────────────────────────────────────────────────────────

export type DriverLicenseStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'SUSPENDED'
  | 'REVOKED'
  | 'EXPIRED'
  | 'ARCHIVED'
  | 'SUPERSEDED'

export type DriverLicenseVerificationStatus =
  | 'PENDING'
  | 'VERIFIED'
  | 'VERIFIED_EXTERNAL'
  | 'REJECTED'
  | 'EXPIRED'

export interface DriverLicense {
  id: string
  driver_id: string
  license_number_redacted: string
  license_number_full: string | null
  country: string
  issuing_authority: string
  issue_date: string | null
  effective_date: string | null
  expiration_date: string | null
  days_until_expiration: number | null
  is_expired: boolean
  is_expiring_soon: boolean
  status: DriverLicenseStatus
  verification_status: DriverLicenseVerificationStatus
  is_primary: boolean
  categories: DriverLicenseCategoryAssignment[]
  restrictions: DriverLicenseRestriction[]
  file_reference_id: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface DriverLicenseCreate {
  license_number: string
  country: string
  issuing_authority: string
  issue_date?: string
  effective_date?: string
  expiration_date: string
  categories: string[]
  restrictions?: DriverLicenseRestrictionCreate[]
  file_reference_id?: string
  notes?: string
  is_primary?: boolean
}

export interface DriverLicenseUpdate {
  country?: string
  issuing_authority?: string
  issue_date?: string
  effective_date?: string
  expiration_date?: string
  categories?: string[]
  notes?: string
}

// ─── License Categories ──────────────────────────────────────────────────────

export type LicenseCategoryStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'RETIRED'
  | 'ARCHIVED'

export type LicenseCategoryScope = 'SYSTEM' | 'ORGANIZATION'

export interface DriverLicenseCategory {
  id: string
  code: string
  name: string
  jurisdiction: string
  group: string
  validity_years: number | null
  status: LicenseCategoryStatus
  scope: LicenseCategoryScope
  version: number
  reference: string | null
  created_at: string
  updated_at: string
}

export interface DriverLicenseCategoryCreate {
  code: string
  name: string
  jurisdiction: string
  group?: string
  validity_years?: number
  reference?: string
}

export interface DriverLicenseCategoryUpdate {
  name?: string
  jurisdiction?: string
  group?: string
  validity_years?: number
  reference?: string
}

export interface DriverLicenseCategoryAssignment {
  id: string
  category_id: string
  category_code: string
  category_name: string
  jurisdiction: string
  validity_years: number | null
  assigned_at: string
  expires_at: string | null
  is_expired: boolean
  status: LicenseCategoryStatus
}

// ─── License Restrictions ────────────────────────────────────────────────────

export type LicenseRestrictionType =
  | 'CORRECTIVE_LENSES'
  | 'DRIVING_TIME_LIMIT'
  | 'GEOGRAPHIC_LIMIT'
  | 'VEHICLE_TYPE_LIMIT'
  | 'TRANSMISSION_LIMIT'
  | 'TIME_OF_DAY_LIMIT'
  | 'MEDICAL_REQUIREMENT'
  | 'OTHER'

export type LicenseRestrictionSeverity =
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL'

export interface DriverLicenseRestriction {
  id: string
  code: string
  type: LicenseRestrictionType
  description_summary: string
  severity: LicenseRestrictionSeverity
  is_blocking: boolean
  effective_date: string
  expiration_date: string | null
  source: string
  status: 'ACTIVE' | 'REVOKED' | 'ARCHIVED'
}

export interface DriverLicenseRestrictionCreate {
  code: string
  type: LicenseRestrictionType
  description_summary: string
  severity: LicenseRestrictionSeverity
  is_blocking?: boolean
  effective_date?: string
  expiration_date?: string
  source?: string
}

// ─── Carrier ─────────────────────────────────────────────────────────────────

export type DriverCarrierAssignmentType =
  | 'PRIMARY'
  | 'SECONDARY'
  | 'TEMPORARY'

export interface DriverCarrierAssignment {
  id: string
  driver_id: string
  carrier_partner_id: string
  carrier_partner_code: string
  carrier_partner_name: string
  carrier_partner_status: string
  assignment_type: DriverCarrierAssignmentType
  relationship_type: string
  start_date: string
  end_date: string | null
  is_active: boolean
  compliance_status: string | null
  created_at: string
  updated_at: string
}

export interface DriverCarrierAssignmentCreate {
  carrier_partner_id: string
  assignment_type: DriverCarrierAssignmentType
  relationship_type?: string
  start_date?: string
  end_date?: string
}

// ─── Contacts ────────────────────────────────────────────────────────────────

export type DriverContactType =
  | 'PHONE'
  | 'EMAIL'
  | 'MOBILE'
  | 'OTHER'

export interface DriverContact {
  id: string
  driver_id: string
  contact_type: DriverContactType
  value_redacted: string
  value_full: string | null
  is_preferred: boolean
  is_primary: boolean
  general_location: string | null
  effective_date: string | null
  expiration_date: string | null
  status: 'ACTIVE' | 'INACTIVE' | 'ARCHIVED'
  created_at: string
  updated_at: string
}

export interface DriverContactCreate {
  contact_type: DriverContactType
  value: string
  is_preferred?: boolean
  is_primary?: boolean
  general_location?: string
  effective_date?: string
  expiration_date?: string
}

export interface DriverContactUpdate {
  contact_type?: DriverContactType
  value?: string
  is_preferred?: boolean
  is_primary?: boolean
  general_location?: string
  effective_date?: string
  expiration_date?: string
}

// ─── Photo ───────────────────────────────────────────────────────────────────

export type DriverPhotoStatus =
  | 'PENDING'
  | 'ACTIVE'
  | 'REVOKED'
  | 'ARCHIVED'
  | 'PENDIENTE_FASE_030'

export interface DriverPhoto {
  id: string
  driver_id: string
  photo_type: string
  source: string
  status: DriverPhotoStatus
  captured_at: string | null
  partial_hash: string | null
  file_reference_id: string | null
  is_current: boolean
  created_at: string
  updated_at: string
}

export interface DriverPhotoReferenceCreate {
  photo_type: string
  source: string
  file_reference_id: string
  captured_at?: string
}

// ─── Documents ────────────────────────────────────────────────────────────────

export type DriverDocumentType =
  | 'IDENTITY_DOCUMENT'
  | 'LICENSE'
  | 'MEDICAL_CERTIFICATE'
  | 'CRIMINAL_RECORD'
  | 'ADDRESS_PROOF'
  | 'TRAINING_CERTIFICATE'
  | 'OTHER'

export type DriverDocumentReviewStatus =
  | 'PENDING'
  | 'VERIFIED'
  | 'REJECTED'
  | 'EXPIRED'

export interface DriverDocument {
  id: string
  driver_id: string
  document_type: DriverDocumentType
  document_type_label: string
  document_number_redacted: string | null
  issuer_name: string | null
  issue_date: string | null
  effective_date: string | null
  expiration_date: string | null
  is_expired: boolean
  days_until_expiration: number | null
  review_status: DriverDocumentReviewStatus
  source: string
  notes: string | null
  file_reference_id: string | null
  created_at: string
  updated_at: string
}

export interface DriverDocumentCreate {
  document_type: DriverDocumentType
  document_number: string
  issuer_name: string
  issue_date?: string
  effective_date?: string
  expiration_date?: string
  notes?: string
  file_reference_id?: string
}

export interface DriverDocumentUpdate {
  document_type?: DriverDocumentType
  document_number?: string
  issuer_name?: string
  issue_date?: string
  effective_date?: string
  expiration_date?: string
  notes?: string
}

export interface DriverDocumentRequirement {
  id: string
  document_type: DriverDocumentType
  document_type_label: string
  is_required: boolean
  is_present: boolean
  is_expired: boolean
  days_until_expiration: number | null
}

// ─── Operational Restrictions ─────────────────────────────────────────────────

export type OperationalRestrictionType =
  | 'DRIVING_HOURS'
  | 'GEOGRAPHIC'
  | 'VEHICLE_TYPE'
  | 'TIME_WINDOW'
  | 'CARGO_TYPE'
  | 'OTHER'

export type OperationalRestrictionSeverity =
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL'

export interface DriverOperationalRestriction {
  id: string
  driver_id: string
  type: OperationalRestrictionType
  severity: OperationalRestrictionSeverity
  is_blocking: boolean
  description_summary: string
  effective_from: string
  effective_until: string | null
  status: 'ACTIVE' | 'REVOKED' | 'ARCHIVED'
  source: string
  created_at: string
  updated_at: string
}

export interface DriverOperationalRestrictionCreate {
  type: OperationalRestrictionType
  severity: OperationalRestrictionSeverity
  is_blocking?: boolean
  description_summary: string
  effective_from?: string
  effective_until?: string
  source?: string
}

// ─── Compliance & Eligibility ─────────────────────────────────────────────────

export interface DriverCompliance {
  driver_id: string
  general_status: DriverComplianceStatus
  identity_valid: boolean
  license_valid: boolean
  categories_valid: boolean
  carrier_valid: boolean
  required_documents_count: number
  present_documents_count: number
  missing_documents_count: number
  expired_documents_count: number
  restrictions_count: number
  blocking_reasons: string[]
  warnings: string[]
  evaluation_date: string
}

export interface DriverEligibility {
  driver_id: string
  status: DriverEligibilityStatus
  license_valid: boolean
  active_categories: string[]
  carrier_valid: boolean
  restrictions_count: number
  documents_complete: boolean
  reasons: string[]
  warnings: string[]
  evaluation_date: string
}

// ─── Vehicle Compatibility ────────────────────────────────────────────────────

export interface DriverVehicleCompatibilityRequest {
  vehicle_id: string
  effective_date?: string
  operation_type?: string
}

export interface DriverVehicleCompatibilityResult {
  driver_id: string
  vehicle_id: string
  eligible: boolean
  requires_review: boolean
  compatible_categories: string[]
  missing_categories: string[]
  restrictions: string[]
  documents: string[]
  blocking_reasons: string[]
  warnings: string[]
  evaluation_date: string
}

// ─── Alerts ───────────────────────────────────────────────────────────────────

export type DriverAlertType =
  | 'LICENSE_EXPIRED'
  | 'LICENSE_EXPIRING_SOON'
  | 'CATEGORY_EXPIRING_SOON'
  | 'DOCUMENT_EXPIRED'
  | 'DOCUMENT_MISSING'
  | 'CARRIER_EXPIRING_SOON'
  | 'RESTRICTION_ACTIVE'
  | 'PHOTO_PENDING'
  | 'REVIEW_REQUIRED'

export type DriverAlertSeverity =
  | 'INFO'
  | 'WARNING'
  | 'CRITICAL'

export type DriverAlertStatus =
  | 'OPEN'
  | 'ACKNOWLEDGED'
  | 'RESOLVED'
  | 'DISMISSED'

export interface DriverAlert {
  id: string
  driver_id: string
  driver_code: string
  driver_name: string
  type: DriverAlertType
  severity: DriverAlertSeverity
  created_at: string
  expiration_date: string | null
  days_remaining: number | null
  carrier_partner_name: string | null
  status: DriverAlertStatus
  can_dismiss: boolean
}

export interface DriverAlertListQuery {
  driver_id?: string
  page?: number
  page_size?: number
  type?: DriverAlertType
  severity?: DriverAlertSeverity
  carrier_partner_id?: string
  status?: DriverAlertStatus
  date_from?: string
  date_to?: string
}

// ─── Versions ────────────────────────────────────────────────────────────────

export type DriverVersionStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'SUPERSEDED'
  | 'ARCHIVED'

export interface DriverVersion {
  id: string
  driver_id: string
  version_number: number
  status: DriverVersionStatus
  identity_redacted: string
  license_redacted: string
  categories: string[]
  carrier_partner_name: string | null
  restrictions_count: number
  compliance_status: DriverComplianceStatus
  eligibility_status: DriverEligibilityStatus
  created_by_name: string
  approved_by_name: string | null
  partial_hash: string
  effective_from: string | null
  effective_until: string | null
  created_at: string
}

export interface DriverVersionComparison {
  field: string
  field_label: string
  old_value: string | null
  new_value: string | null
  change_type: 'ADDED' | 'REMOVED' | 'CHANGED' | 'CRITICAL_CHANGE'
  is_critical: boolean
}

// ─── Duplicates ───────────────────────────────────────────────────────────────

export interface DriverDuplicateCandidate {
  id: string
  internal_code: string
  full_name: string
  document_number_redacted: string
  license_number_redacted: string | null
  carrier_partner_name: string | null
  lifecycle_status: DriverLifecycleStatus
  match_reasons: string[]
}

export interface DriverDuplicateCheckRequest {
  document_number?: string
  license_number?: string
  full_name?: string
  birth_date?: string
}

// ─── History ───────────────────────────────────────────────────────────────────

export type DriverHistoryEventType =
  | 'CREATED'
  | 'VALIDATED'
  | 'ACTIVATED'
  | 'SUSPENDED'
  | 'BLOCKED'
  | 'UNBLOCKED'
  | 'RETIRED'
  | 'DOCUMENT_REGISTERED'
  | 'DOCUMENT_PRIMARY_CHANGED'
  | 'LICENSE_CREATED'
  | 'LICENSE_RENEWED'
  | 'LICENSE_EXPIRED'
  | 'CATEGORY_ASSIGNED'
  | 'CARRIER_CHANGED'
  | 'CONTACT_UPDATED'
  | 'PHOTO_REPLACED'
  | 'DOCUMENT_EXPIRED'
  | 'RESTRICTION_CREATED'
  | 'RESTRICTION_REVOKED'
  | 'VERSION_ACTIVATED'
  | 'COMPATIBILITY_EVALUATED'

export interface DriverHistoryEvent {
  id: string
  driver_id: string
  event_type: DriverHistoryEventType
  action_description: string
  result: string
  reason: string | null
  resource_type: string | null
  resource_id: string | null
  version_number: number | null
  user_name: string
  created_at: string
}

// ─── Capabilities ─────────────────────────────────────────────────────────────

export interface DriverCapabilities {
  can_view: boolean
  can_create: boolean
  can_update: boolean
  can_activate: boolean
  can_deactivate: boolean
  can_suspend: boolean
  can_block: boolean
  can_unblock: boolean
  can_retire: boolean
  can_archive: boolean
  can_view_sensitive_identity: boolean
  can_manage_identity: boolean
  can_manage_licenses: boolean
  can_manage_categories: boolean
  can_manage_carrier: boolean
  can_manage_contacts: boolean
  can_view_photo: boolean
  can_manage_photo: boolean
  can_manage_documents: boolean
  can_manage_restrictions: boolean
  can_view_history: boolean
  can_create_version: boolean
  can_activate_version: boolean
  can_evaluate_vehicle_compatibility: boolean
}

// ─── Main Driver Entities ─────────────────────────────────────────────────────

export interface Driver {
  id: string
  internal_code: string
  first_name: string
  second_name: string | null
  paternal_surname: string
  maternal_surname: string | null
  full_name: string
  birth_date: string | null
  nationality: string | null
  identity_document_type: DriverIdentityDocumentType | null
  identity_document_number_redacted: string
  identity_document_number_full: string | null
  identity_verification_status: DriverIdentityVerificationStatus
  primary_license_number_redacted: string | null
  primary_license_expiration: string | null
  primary_license_days_until_expiration: number | null
  primary_license_is_expired: boolean
  primary_license_is_expiring_soon: boolean
  primary_license_categories: string[]
  carrier_partner_id: string | null
  carrier_partner_name: string | null
  carrier_partner_code: string | null
  lifecycle_status: DriverLifecycleStatus
  compliance_status: DriverComplianceStatus
  eligibility_status: DriverEligibilityStatus
  has_photo: boolean
  photo_status: DriverPhotoStatus
  restrictions_count: number
  active_version_number: number
  capabilities: DriverCapabilities
  created_by_user_name: string
  created_at: string
  updated_at: string
}

export interface DriverSummary {
  id: string
  internal_code: string
  full_name: string
  identity_document_number_redacted: string
  primary_license_number_redacted: string | null
  primary_license_categories: string[]
  primary_license_expiration: string | null
  primary_license_is_expired: boolean
  primary_license_is_expiring_soon: boolean
  carrier_partner_name: string | null
  lifecycle_status: DriverLifecycleStatus
  compliance_status: DriverComplianceStatus
  eligibility_status: DriverEligibilityStatus
  has_photo: boolean
  restrictions_count: number
  updated_at: string
}

export interface DriverCreate {
  first_name: string
  second_name?: string
  paternal_surname: string
  maternal_surname?: string
  birth_date?: string
  nationality?: string
  identity_document_type: DriverIdentityDocumentType
  identity_document_number: string
  notes?: string
}

export interface DriverUpdate {
  first_name?: string
  second_name?: string
  paternal_surname?: string
  maternal_surname?: string
  birth_date?: string
  nationality?: string
  notes?: string
}

export interface DriverListQuery {
  page?: number
  page_size?: number
  search?: string
  carrier_partner_id?: string
  license_category?: string
  lifecycle_status?: DriverLifecycleStatus
  compliance_status?: DriverComplianceStatus
  eligibility_status?: DriverEligibilityStatus
  license_expired?: boolean
  license_expiring_soon?: boolean
  documents_incomplete?: boolean
  has_restrictions?: boolean
  has_photo?: boolean
  has_user_account?: boolean
  created_from?: string
  created_to?: string
}

export interface DriverStats {
  total_drivers: number
  active_count: number
  eligible_count: number
  restricted_count: number
  licenses_expiring_soon_count: number
  licenses_expired_count: number
  documents_incomplete_count: number
  blocked_count: number
}

export type PaginatedDrivers = PaginatedResponse<DriverSummary>
export type PaginatedDriverAlerts = PaginatedResponse<DriverAlert>