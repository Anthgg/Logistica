import { apiRequest, getCsrfToken } from './api-client'
import type { ListQuery, PaginatedResponse } from '../types/logistics-resources'
import type {
  BusinessPartner,
  BusinessPartnerAddress,
  BusinessPartnerContact,
  BusinessPartnerCreate,
  BusinessPartnerDocument,
  BusinessPartnerEvaluation,
} from '../types/business-partners'

interface BackendBusinessPartner {
  id: string
  organization_id: string
  partner_code: string
  legal_name: string
  trade_name: string | null
  person_type: string
  country_code: string
  status: string
  lifecycle_status: string
  risk_status: string
  compliance_status: string
  row_version: number
  created_at: string
  updated_at: string
}

function normalizePartner(partner: BackendBusinessPartner): BusinessPartner {
  return {
    id: partner.id,
    code: partner.partner_code,
    legal_name: partner.legal_name,
    trade_name: partner.trade_name,
    tax_id: '',
    tax_id_status: 'NOT_VERIFIED',
    country_code: partner.country_code,
    roles: [],
    status: partner.status as BusinessPartner['status'],
    risk_level: (partner.risk_status === 'NORMAL' ? 'LOW' : partner.risk_status) as BusinessPartner['risk_level'],
    compliance_status: partner.compliance_status as BusinessPartner['compliance_status'],
    primary_address: null,
    primary_contact: null,
    created_at: partner.created_at,
    updated_at: partner.updated_at,
    capabilities: {
      can_view: true,
      can_create: false,
      can_update: false,
      can_activate: false,
      can_suspend: false,
      can_block: false,
      can_unblock: false,
      can_archive: false,
      can_manage_roles: false,
      can_manage_identifiers: false,
      can_manage_addresses: false,
      can_manage_contacts: false,
      can_manage_evaluations: false,
      can_approve_evaluations: false,
      can_manage_documents: false,
      can_verify_documents: false,
      can_view_sensitive: false,
      can_view_history: false,
      can_create_version: false,
      can_activate_version: false,
    },
  }
}

export const businessPartnersApi = {
  async list(query?: ListQuery): Promise<PaginatedResponse<BusinessPartner>> {
    const params = new URLSearchParams()
    if (query?.search) params.set('search', query.search)
    if (query?.status) params.set('status', query.status)
    if (query?.role) params.set('role', query.role)
    const qs = params.toString()
    const response = await apiRequest<BackendBusinessPartner[]>({
      path: `/logistics/business-partners${qs ? `?${qs}` : ''}`,
    })
    const page = query?.page ?? 1
    const pageSize = query?.page_size ?? Math.max(response.length, 1)
    const start = (page - 1) * pageSize
    const items = response.map(normalizePartner)
    return {
      items: items.slice(start, start + pageSize),
      page,
      page_size: pageSize,
      total: items.length,
      total_pages: Math.max(Math.ceil(items.length / pageSize), 1),
    }
  },

  async get(id: string): Promise<BusinessPartner> {
    const response = await apiRequest<BackendBusinessPartner>({
      path: `/logistics/business-partners/${id}`,
    })
    return normalizePartner(response)
  },

  async create(data: BusinessPartnerCreate): Promise<BusinessPartner> {
    const csrfToken = await getCsrfToken()
    const response = await apiRequest<BackendBusinessPartner>({
      path: '/logistics/business-partners',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        legal_name: data.legal_name,
        trade_name: data.trade_name || null,
        person_type: 'LEGAL_ENTITY',
        country_code: data.country_code,
        tax_id_type: data.country_code === 'PE' ? 'RUC' : 'OTHER',
        tax_id_value: data.tax_id,
        roles: data.roles,
      },
    })
    return normalizePartner(response)
  },

  async block(id: string, reason: string): Promise<BusinessPartner> {
    const csrfToken = await getCsrfToken()
    const response = await apiRequest<BackendBusinessPartner>({
      path: `/logistics/business-partners/${id}/block?reason=${encodeURIComponent(reason)}`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
    return normalizePartner(response)
  },

  async unblock(id: string, _reason: string): Promise<BusinessPartner> {
    const csrfToken = await getCsrfToken()
    const response = await apiRequest<BackendBusinessPartner>({
      path: `/logistics/business-partners/${id}/activate`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {},
    })
    return normalizePartner(response)
  },

  async listAddresses(_partnerId: string): Promise<BusinessPartnerAddress[]> {
    return []
  },

  async listContacts(_partnerId: string): Promise<BusinessPartnerContact[]> {
    return []
  },

  async listEvaluations(_partnerId: string): Promise<BusinessPartnerEvaluation[]> {
    return []
  },

  async listDocuments(_partnerId: string): Promise<BusinessPartnerDocument[]> {
    return []
  },
}
