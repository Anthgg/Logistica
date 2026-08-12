import { apiRequest, getCsrfToken } from './api-client'
import type { PaginatedResponse } from '../types/logistics-resources'
import type {
  Vehicle,
  VehicleCapacityProfile,
  VehicleCapacityProfileCreate,
  VehicleCarrierAssignment,
  VehicleCompliance,
  VehicleCreate,
  VehicleDocument,
  VehicleDocumentCreate,
  VehicleDuplicateCandidate,
  VehicleListQuery,
  VehicleMake,
  VehicleMakeCreate,
  VehicleMakeUpdate,
  VehicleModel,
  VehicleModelCreate,
  VehicleModelUpdate,
  VehicleOwnershipAssignment,
  VehiclePlateAssignment,
  VehicleStats,
  VehicleSummary,
  VehicleUpdate,
  VehicleVersion,
} from '../types/vehicles'

const BASE = '/logistics/vehicles'

type BackendVehicle = {
  id: string
  vehicle_code: string
  display_plate: string
  normalized_plate: string
  masked_vin?: string | null
  make_id: string
  model_id: string
  manufacturing_year?: number | null
  vehicle_type: string
  body_type: string
  lifecycle_status: string
  operational_status: string
  compliance_status: string
  created_at: string
  updated_at: string
}

type BackendMake = {
  id: string
  code: string
  name: string
  country_code?: string | null
  status: string
  system_defined: boolean
}

type BackendModel = {
  id: string
  make_id: string
  code: string
  name: string
  vehicle_type?: string | null
  body_type?: string | null
  status: string
  system_defined: boolean
}

function normalizeVehicle(raw: BackendVehicle): Vehicle {
  return {
    id: raw.id,
    internal_code: raw.vehicle_code,
    plate_number: raw.display_plate,
    normalized_plate: raw.normalized_plate,
    country_of_registration: 'PE',
    jurisdiction: null,
    vin: raw.masked_vin ?? null,
    is_vin_masked: Boolean(raw.masked_vin),
    chassis_number: null,
    engine_number: null,
    make_id: raw.make_id,
    make_name: raw.make_id,
    model_id: raw.model_id,
    model_name: raw.model_id,
    year_of_manufacture: raw.manufacturing_year ?? new Date().getFullYear(),
    model_year: null,
    vehicle_type: raw.vehicle_type as Vehicle['vehicle_type'],
    vehicle_type_label: raw.vehicle_type,
    body_type: raw.body_type as Vehicle['body_type'],
    body_type_label: raw.body_type,
    fuel_type: 'OTHER',
    transmission_type: null,
    axles_count: 0,
    wheels_count: null,
    color: null,
    notes: null,
    lifecycle_status: raw.lifecycle_status as Vehicle['lifecycle_status'],
    operational_status: raw.operational_status as Vehicle['operational_status'],
    compliance_status: raw.compliance_status as Vehicle['compliance_status'],
    current_owner_name: null,
    current_carrier_id: null,
    current_carrier_name: null,
    current_capacity_summary: null,
    active_version_number: 1,
    capabilities: {
      can_view: true,
      can_create: true,
      can_update: false,
      can_activate: true,
      can_deactivate: false,
      can_suspend: false,
      can_block: true,
      can_unblock: true,
      can_retire: false,
      can_archive: false,
      can_change_plate: true,
      can_view_VIN: true,
      can_manage_capacity: true,
      can_manage_ownership: false,
      can_manage_carrier: true,
      can_manage_documents: true,
      can_review_documents: false,
      can_view_history: false,
      can_create_version: false,
      can_activate_version: false,
    },
    created_by_user_name: '',
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  }
}

function normalizeMake(raw: BackendMake): VehicleMake {
  return {
    id: raw.id,
    code: raw.code,
    name: raw.name,
    country_of_origin: raw.country_code ?? null,
    scope: raw.system_defined ? 'SYSTEM' : 'ORGANIZATION',
    is_active: raw.status === 'ACTIVE',
    models_count: 0,
    created_at: '',
  }
}

function normalizeModel(raw: BackendModel, makeName = ''): VehicleModel {
  return {
    id: raw.id,
    make_id: raw.make_id,
    make_name: makeName,
    code: raw.code,
    name: raw.name,
    suggested_vehicle_type: raw.vehicle_type as VehicleModel['suggested_vehicle_type'],
    suggested_body_type: raw.body_type as VehicleModel['suggested_body_type'],
    production_start_year: null,
    production_end_year: null,
    is_active: raw.status === 'ACTIVE',
    created_at: '',
  }
}

function unsupported(operation: string): never {
  throw new Error(`${operation} no está disponible en la versión actual del backend.`)
}

export const vehiclesApi = {
  // ── Vehicle CRUD ──────────────────────────────────────────────────────────

  async list(query?: VehicleListQuery): Promise<PaginatedResponse<VehicleSummary>> {
    return {
      items: [],
      page: query?.page ?? 1,
      page_size: query?.page_size ?? 20,
      total: 0,
      total_pages: 0,
    }
  },

  async get(id: string): Promise<Vehicle> {
    const raw = await apiRequest<BackendVehicle>({ path: `${BASE}/${id}` })
    return normalizeVehicle(raw)
  },

  async getStats(): Promise<VehicleStats> {
    return {
      total_vehicles: 0,
      active_count: 0,
      available_count: 0,
      blocked_count: 0,
      documents_expired_count: 0,
      maintenance_count: 0,
    }
  },

  async create(data: VehicleCreate): Promise<Vehicle> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendVehicle>({
      path: BASE,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        display_plate: data.plate_number,
        make_id: data.make_id,
        model_id: data.model_id,
        vehicle_code: data.internal_code,
        vin: data.vin,
        chassis_number: data.chassis_number,
        engine_number: data.engine_number,
        manufacturing_year: data.year_of_manufacture,
        vehicle_type: data.vehicle_type,
        body_type: data.body_type,
        notes: data.notes,
      },
    })
    return normalizeVehicle(raw)
  },

  async update(_id: string, _data: VehicleUpdate): Promise<Vehicle> {
    return unsupported('La edición de vehículos')
  },

  // ── Transitions ───────────────────────────────────────────────────────────

  async activate(id: string): Promise<Vehicle> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendVehicle>({
      path: `${BASE}/${id}/activate`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
    return normalizeVehicle(raw)
  },

  async deactivate(_id: string, _reason: string): Promise<Vehicle> {
    return unsupported('La desactivación de vehículos')
  },

  async suspend(_id: string, _reason: string): Promise<Vehicle> {
    return unsupported('La suspensión de vehículos')
  },

  async block(id: string, reason: string): Promise<Vehicle> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendVehicle>({
      path: `${BASE}/${id}/block`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason },
    })
    return normalizeVehicle(raw)
  },

  async unblock(id: string, reason: string): Promise<Vehicle> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendVehicle>({
      path: `${BASE}/${id}/unblock`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
    void reason
    return normalizeVehicle(raw)
  },

  async retire(_id: string, _reason: string): Promise<Vehicle> {
    return unsupported('El retiro de vehículos')
  },

  // ── Plate & VIN ───────────────────────────────────────────────────────────

  async previewPlateChange(id: string, newPlate: string): Promise<{ normalized_plate: string; warnings: string[]; conflicts: string[] }> {
    void id
    return {
      normalized_plate: newPlate.toUpperCase().replace(/[^A-Z0-9]/g, ''),
      warnings: [],
      conflicts: [],
    }
  },

  async changePlate(id: string, newPlate: string, reason: string): Promise<Vehicle> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendVehicle>({
      path: `${BASE}/${id}/plate-change`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { new_display_plate: newPlate, reason },
    })
    return normalizeVehicle(raw)
  },

  async listPlates(_id: string): Promise<VehiclePlateAssignment[]> {
    return []
  },

  async checkDuplicates(_data: { plate_number?: string; vin?: string; chassis_number?: string }): Promise<VehicleDuplicateCandidate[]> {
    return []
  },

  async getCompliance(_id: string): Promise<VehicleCompliance> {
    return unsupported('El resumen de cumplimiento vehicular')
  },

  // ── Capacity Profiles ─────────────────────────────────────────────────────

  async listCapacityProfiles(_vehicleId: string): Promise<VehicleCapacityProfile[]> {
    return []
  },

  async createCapacityProfile(vehicleId: string, data: VehicleCapacityProfileCreate): Promise<VehicleCapacityProfile> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${vehicleId}/capacity-profiles`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        max_gross_weight: data.gross_weight,
        max_gross_weight_unit_id: data.gross_weight_unit_id,
        tare_weight: data.tare_weight,
        tare_weight_unit_id: data.tare_weight_unit_id,
        max_payload: data.payload_capacity,
        max_payload_unit_id: data.payload_capacity_unit_id,
        max_volume: data.volume_capacity,
        max_volume_unit_id: data.volume_capacity_unit_id,
        pallet_positions: data.pallet_positions,
        axle_count: data.axles_count,
      },
    })
  },

  // ── Ownership & Carrier Assignments ──────────────────────────────────────

  async listOwnershipAssignments(_vehicleId: string): Promise<VehicleOwnershipAssignment[]> {
    return []
  },

  async listCarrierAssignments(_vehicleId: string): Promise<VehicleCarrierAssignment[]> {
    return []
  },

  async assignCarrier(vehicleId: string, carrierPartnerId: string, assignmentType: 'PRIMARY' | 'SECONDARY' | 'TEMPORARY', reason: string): Promise<VehicleCarrierAssignment> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${vehicleId}/carrier-assignments`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        carrier_business_partner_id: carrierPartnerId,
        assignment_type: assignmentType,
        authorization_reference: reason,
      },
    })
  },

  // ── Vehicle Documents ─────────────────────────────────────────────────────

  async listDocuments(vehicleId: string): Promise<VehicleDocument[]> {
    return apiRequest({ path: `${BASE}/${vehicleId}/documents` })
  },

  async createDocument(vehicleId: string, data: VehicleDocumentCreate): Promise<VehicleDocument> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${vehicleId}/documents`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        document_type: data.document_type,
        document_number: data.document_number,
        issuer: data.issuer_name,
        issued_at: data.issue_date,
        valid_from: data.effective_date,
        expires_at: data.expiration_date,
        file_reference_id: data.file_reference_id,
        notes: data.notes,
      },
    })
  },

  // ── Versions & History ────────────────────────────────────────────────────

  async listVersions(_vehicleId: string): Promise<VehicleVersion[]> {
    return []
  },

  async getHistory(_vehicleId: string): Promise<Array<{ id: string; event_type: string; action_description: string; user_name: string; created_at: string }>> {
    return []
  },

  // ── Vehicle Makes & Models ────────────────────────────────────────────────

  async listMakes(): Promise<VehicleMake[]> {
    const raw = await apiRequest<BackendMake[]>({ path: '/logistics/vehicle-makes' })
    return raw.map(normalizeMake)
  },

  async createMake(data: VehicleMakeCreate): Promise<VehicleMake> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendMake>({
      path: '/logistics/vehicle-makes',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        code: data.code,
        name: data.name,
        country_code: data.country_of_origin,
      },
    })
    return normalizeMake(raw)
  },

  async updateMake(_id: string, _data: VehicleMakeUpdate): Promise<VehicleMake> {
    return unsupported('La edición de marcas')
  },

  async listModels(makeId?: string): Promise<VehicleModel[]> {
    if (!makeId) return []
    const raw = await apiRequest<BackendModel[]>({
      path: `/logistics/vehicle-makes/${makeId}/models`,
    })
    return raw.map((model) => normalizeModel(model))
  },

  async createModel(data: VehicleModelCreate): Promise<VehicleModel> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendModel>({
      path: '/logistics/vehicle-models',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        make_id: data.make_id,
        code: data.code,
        name: data.name,
        vehicle_type: data.suggested_vehicle_type,
        body_type: data.suggested_body_type,
      },
    })
    return normalizeModel(raw)
  },

  async updateModel(_id: string, _data: VehicleModelUpdate): Promise<VehicleModel> {
    return unsupported('La edición de modelos')
  },
}
