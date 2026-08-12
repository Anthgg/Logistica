// ─── Vehicle Master – TypeScript strict types ────────────────────────────────

export type VehicleLifecycleStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'INACTIVE'
  | 'SUSPENDED'
  | 'RETIRED'
  | 'ARCHIVED'

export type VehicleOperationalStatus =
  | 'UNEVALUATED'
  | 'AVAILABLE'
  | 'UNAVAILABLE'
  | 'UNDER_REVIEW'
  | 'MAINTENANCE'
  | 'DOCUMENTS_EXPIRED'
  | 'DOCUMENTS_INCOMPLETE'
  | 'BLOCKED'
  | 'OUT_OF_SERVICE'
  | 'RETIRED'

export type VehicleComplianceStatus =
  | 'COMPLIANT'
  | 'PARTIAL'
  | 'NON_COMPLIANT'
  | 'DOCUMENTS_EXPIRED'
  | 'UNDER_REVIEW'

export type VehicleType =
  | 'TRUCK'
  | 'TRACTOR'
  | 'TRAILER'
  | 'VAN'
  | 'PICKUP'
  | 'TANKER'
  | 'REFRIGERATED'
  | 'CONTAINER_CHASSIS'
  | 'OTHER'

export type VehicleBodyType =
  | 'CLOSED'
  | 'OPEN'
  | 'REFRIGERATED'
  | 'TANK'
  | 'FLATBED'
  | 'SIDE_CURTAIN'
  | 'CURTAINSIDE'
  | 'CONTAINER_CARRIER'
  | 'OTHER'

export type VehicleFuelType =
  | 'DIESEL'
  | 'GASOLINE'
  | 'GLP'
  | 'GNV'
  | 'ELECTRIC'
  | 'HYBRID'
  | 'OTHER'

export type VehicleTransmissionType =
  | 'MANUAL'
  | 'AUTOMATIC'
  | 'AUTOMATED_MANUAL'

export type VehicleOwnershipType =
  | 'OWNED'
  | 'LEASED'
  | 'THIRD_PARTY'
  | 'RENTED'

export type VehicleDocumentType =
  | 'PROPERTY_CARD'
  | 'PROPERTY_TITLE'
  | 'SOAT'
  | 'INSURANCE_POLICY'
  | 'TECHNICAL_INSPECTION'
  | 'TRANSPORT_PERMIT'
  | 'OPERATIONAL_PERMIT'
  | 'REFRIGERATION_CERTIFICATE'
  | 'HAZMAT_CERTIFICATE'
  | 'WEIGHT_CERTIFICATE'
  | 'OTHER'

// ─── Makes & Models ─────────────────────────────────────────────────────────

export interface VehicleMake {
  id: string
  code: string
  name: string
  country_of_origin: string | null
  scope: 'SYSTEM' | 'ORGANIZATION'
  is_active: boolean
  models_count: number
  created_at: string
}

export interface VehicleMakeCreate {
  code: string
  name: string
  country_of_origin?: string
}

export interface VehicleMakeUpdate {
  name?: string
  country_of_origin?: string
  is_active?: boolean
}

export interface VehicleModel {
  id: string
  make_id: string
  make_name: string
  code: string
  name: string
  suggested_vehicle_type: VehicleType | null
  suggested_body_type: VehicleBodyType | null
  production_start_year: number | null
  production_end_year: number | null
  is_active: boolean
  created_at: string
}

export interface VehicleModelCreate {
  make_id: string
  code: string
  name: string
  suggested_vehicle_type?: VehicleType
  suggested_body_type?: VehicleBodyType
  production_start_year?: number
  production_end_year?: number
}

export interface VehicleModelUpdate {
  name?: string
  suggested_vehicle_type?: VehicleType
  suggested_body_type?: VehicleBodyType
  production_start_year?: number
  production_end_year?: number
  is_active?: boolean
}

// ─── Sub-entities ───────────────────────────────────────────────────────────

export interface VehicleCapacityProfile {
  id: string
  vehicle_id: string
  gross_weight: string // decimal string
  gross_weight_unit_id: string
  gross_weight_unit_code: string
  tare_weight: string // decimal string
  tare_weight_unit_id: string
  tare_weight_unit_code: string
  payload_capacity: string // decimal string
  payload_capacity_unit_id: string
  payload_capacity_unit_code: string
  volume_capacity: string // decimal string
  volume_capacity_unit_id: string
  volume_capacity_unit_code: string
  pallet_positions: number
  max_units: number
  passenger_capacity: number
  axles_count: number
  source_reference: string | null
  is_active: boolean
  version: number
  created_at: string
}

export interface VehicleCapacityProfileCreate {
  gross_weight: string
  gross_weight_unit_id: string
  tare_weight: string
  tare_weight_unit_id: string
  payload_capacity: string
  payload_capacity_unit_id: string
  volume_capacity: string
  volume_capacity_unit_id: string
  pallet_positions?: number
  max_units?: number
  passenger_capacity?: number
  axles_count?: number
  source_reference?: string
}

export interface VehicleDimensions {
  exterior_length: string // decimal string
  exterior_width: string
  exterior_height: string
  interior_length: string | null
  interior_width: string | null
  interior_height: string | null
  length_unit_code: string
  reported_volume: string | null
  calculated_volume: string | null
  volume_unit_code: string
  measurement_date: string | null
}

export interface VehicleOwnershipAssignment {
  id: string
  vehicle_id: string
  ownership_type: VehicleOwnershipType
  owner_partner_id: string | null
  owner_partner_name: string | null
  start_date: string // ISO date
  end_date: string | null
  contract_reference: string | null
  is_active: boolean
  created_at: string
}

export interface VehicleCarrierAssignment {
  id: string
  vehicle_id: string
  carrier_partner_id: string
  carrier_partner_code: string
  carrier_partner_name: string
  carrier_status: string
  start_date: string
  end_date: string | null
  assignment_type: 'PRIMARY' | 'SECONDARY' | 'TEMPORARY'
  is_active: boolean
  created_at: string
}

export interface VehicleDocument {
  id: string
  vehicle_id: string
  document_type: VehicleDocumentType
  document_type_label: string
  document_number: string
  issuer_name: string
  issue_date: string | null
  effective_date: string | null
  expiration_date: string | null
  is_expired: boolean
  days_until_expiration: number | null
  review_status: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'EXPIRED'
  source: string
  notes: string | null
  file_reference_id: string | null
  created_at: string
}

export interface VehicleDocumentCreate {
  document_type: VehicleDocumentType
  document_number: string
  issuer_name: string
  issue_date?: string
  effective_date?: string
  expiration_date?: string
  notes?: string
  file_reference_id?: string
}

export interface VehiclePlateAssignment {
  id: string
  vehicle_id: string
  plate_number: string
  normalized_plate: string
  is_current: boolean
  start_date: string
  end_date: string | null
  change_reason: string | null
  created_at: string
}

export interface VehicleVersion {
  id: string
  vehicle_id: string
  version_number: number
  status: 'DRAFT' | 'ACTIVE' | 'SUPERSEDED'
  plate_number: string
  make_name: string
  model_name: string
  vehicle_type: VehicleType
  created_by_name: string
  approved_by_name: string | null
  partial_hash: string
  created_at: string
}

export interface VehicleDuplicateCandidate {
  id: string
  internal_code: string
  plate_number: string
  vin: string | null
  make_name: string
  model_name: string
  year_of_manufacture: number
  status: VehicleLifecycleStatus
  match_reasons: string[]
}

export interface VehicleCompliance {
  vehicle_id: string
  general_status: VehicleComplianceStatus
  operational_status: VehicleOperationalStatus
  is_owner_valid: boolean
  is_carrier_valid: boolean
  is_capacity_configured: boolean
  required_documents_count: number
  present_documents_count: number
  missing_documents_count: number
  expired_documents_count: number
  expiring_soon_documents_count: number
  blocking_reasons: string[]
  warnings: string[]
  evaluation_date: string
}

export interface VehicleCapabilities {
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
  can_change_plate: boolean
  can_view_VIN: boolean
  can_manage_capacity: boolean
  can_manage_ownership: boolean
  can_manage_carrier: boolean
  can_manage_documents: boolean
  can_review_documents: boolean
  can_view_history: boolean
  can_create_version: boolean
  can_activate_version: boolean
}

// ─── Main Vehicle Entities ──────────────────────────────────────────────────

export interface Vehicle {
  id: string
  internal_code: string
  plate_number: string // decimal / raw string
  normalized_plate: string
  country_of_registration: string
  jurisdiction: string | null
  vin: string | null // string or masked
  is_vin_masked: boolean
  chassis_number: string | null
  engine_number: string | null
  make_id: string
  make_name: string
  model_id: string
  model_name: string
  year_of_manufacture: number
  model_year: number | null
  vehicle_type: VehicleType
  vehicle_type_label: string
  body_type: VehicleBodyType
  body_type_label: string
  fuel_type: VehicleFuelType
  transmission_type: VehicleTransmissionType | null
  axles_count: number
  wheels_count: number | null
  color: string | null
  notes: string | null
  lifecycle_status: VehicleLifecycleStatus
  operational_status: VehicleOperationalStatus
  compliance_status: VehicleComplianceStatus
  current_owner_name: string | null
  current_carrier_id: string | null
  current_carrier_name: string | null
  current_capacity_summary: string | null
  active_version_number: number
  capabilities: VehicleCapabilities
  created_by_user_name: string
  created_at: string
  updated_at: string
}

export interface VehicleSummary {
  id: string
  internal_code: string
  plate_number: string
  make_name: string
  model_name: string
  year_of_manufacture: number
  vehicle_type: VehicleType
  vehicle_type_label: string
  lifecycle_status: VehicleLifecycleStatus
  operational_status: VehicleOperationalStatus
  compliance_status: VehicleComplianceStatus
  current_owner_name: string | null
  current_carrier_name: string | null
  payload_capacity_summary: string | null
  documents_expired_count: number
  updated_at: string
}

export interface VehicleCreate {
  internal_code?: string
  plate_number: string
  country_of_registration?: string
  jurisdiction?: string
  vin?: string
  chassis_number?: string
  engine_number?: string
  make_id: string
  model_id: string
  year_of_manufacture: number
  model_year?: number
  vehicle_type: VehicleType
  body_type: VehicleBodyType
  fuel_type?: VehicleFuelType
  transmission_type?: VehicleTransmissionType
  axles_count?: number
  wheels_count?: number
  color?: string
  notes?: string
}

export interface VehicleUpdate {
  country_of_registration?: string
  jurisdiction?: string
  vin?: string
  chassis_number?: string
  engine_number?: string
  make_id?: string
  model_id?: string
  year_of_manufacture?: number
  model_year?: number
  vehicle_type?: VehicleType
  body_type?: VehicleBodyType
  fuel_type?: VehicleFuelType
  transmission_type?: VehicleTransmissionType
  axles_count?: number
  wheels_count?: number
  color?: string
  notes?: string
}

export interface VehicleListQuery {
  page?: number
  page_size?: number
  search?: string
  make_id?: string
  model_id?: string
  vehicle_type?: VehicleType
  body_type?: VehicleBodyType
  lifecycle_status?: VehicleLifecycleStatus
  operational_status?: VehicleOperationalStatus
  compliance_status?: VehicleComplianceStatus
  owner_partner_id?: string
  carrier_partner_id?: string
  has_expired_documents?: boolean
  min_payload_capacity?: string
  min_volume_capacity?: string
  year?: number
}

export interface VehicleStats {
  total_vehicles: number
  active_count: number
  available_count: number
  blocked_count: number
  documents_expired_count: number
  maintenance_count: number
}
