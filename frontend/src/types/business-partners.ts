export type BusinessPartnerRoleType = 'SUPPLIER' | 'CUSTOMER' | 'CARRIER'

export type BusinessPartnerStatus = 'DRAFT' | 'ACTIVE' | 'SUSPENDED' | 'BLOCKED' | 'ARCHIVED'

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type ComplianceStatus = 'COMPLIANT' | 'WARNING' | 'NON_COMPLIANT' | 'PENDING_REVIEW'

export interface BusinessPartnerCapabilities {
  can_view: boolean
  can_create: boolean
  can_update: boolean
  can_activate: boolean
  can_suspend: boolean
  can_block: boolean
  can_unblock: boolean
  can_archive: boolean
  can_manage_roles: boolean
  can_manage_identifiers: boolean
  can_manage_addresses: boolean
  can_manage_contacts: boolean
  can_manage_evaluations: boolean
  can_approve_evaluations: boolean
  can_manage_documents: boolean
  can_verify_documents: boolean
  can_view_sensitive: boolean
  can_view_history: boolean
  can_create_version: boolean
  can_activate_version: boolean
}

export interface BusinessPartner {
  id: string
  code: string
  legal_name: string
  trade_name: string | null
  tax_id: string
  tax_id_status: 'FORMAT_VALID' | 'NOT_VERIFIED' | 'VERIFIED_EXTERNAL'
  country_code: string
  roles: BusinessPartnerRoleType[]
  status: BusinessPartnerStatus
  risk_level: RiskLevel
  compliance_status: ComplianceStatus
  primary_address: string | null
  primary_contact: string | null
  created_at: string
  updated_at: string
  capabilities: BusinessPartnerCapabilities
}

export interface BusinessPartnerCreate {
  code?: string
  legal_name: string
  trade_name?: string
  tax_id: string
  country_code: string
  roles: BusinessPartnerRoleType[]
}

export interface BusinessPartnerRole {
  id: string
  partner_id: string
  role_type: BusinessPartnerRoleType
  status: 'ACTIVE' | 'SUSPENDED' | 'ARCHIVED'
  created_at: string
}

export interface BusinessPartnerAddress {
  id: string
  partner_id: string
  address_type: 'FISCAL' | 'DELIVERY' | 'BILLING' | 'PICKUP'
  street: string
  district: string
  province: string
  department: string
  country_code: string
  is_primary: boolean
  is_active: boolean
}

export interface BusinessPartnerContact {
  id: string
  partner_id: string
  full_name: string
  role_title: string
  email: string
  phone: string
  is_primary: boolean
  receives_procurement_docs: boolean
  receives_delivery_alerts: boolean
}

export interface BusinessPartnerEvaluation {
  id: string
  partner_id: string
  period: string
  score: string
  risk_level: RiskLevel
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED'
  evaluated_by: string
  approved_by: string | null
  evaluated_at: string
}

export interface BusinessPartnerDocument {
  id: string
  partner_id: string
  doc_type: 'TAX_CERTIFICATE' | 'OPERATING_PERMIT' | 'INSURANCE' | 'IDENTITY'
  doc_number: string
  expiration_date: string | null
  is_expired: boolean
  status: 'REGISTERED' | 'VERIFIED' | 'REJECTED'
}
