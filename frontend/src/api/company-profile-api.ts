import { apiRequest, getCsrfToken } from './api-client'
import { API_ROOT } from './config'
import type {
  AuthorizedSigner,
  AuthorizedSignerCreate,
  CompanyProfile,
  CompanyProfileUpdate,
  InstitutionalPreviewRequest,
  NumberingPolicy,
  NumberingPolicyCreate,
  OrganizationAddress,
  OrganizationAddressCreate,
  OrganizationAsset,
  OrganizationContact,
  OrganizationContactCreate,
  ProfileVersionItem,
} from '../types/company-profile'
import type { ListQuery, PaginatedResponse } from '../types/logistics-resources'

export const companyProfileApi = {
  async getProfile(): Promise<CompanyProfile> {
    return apiRequest({
      path: '/logistics/company-profile',
    })
  },

  async updateProfile(data: CompanyProfileUpdate): Promise<CompanyProfile> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/company-profile',
      method: 'PATCH',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async listVersions(): Promise<ProfileVersionItem[]> {
    return apiRequest<ProfileVersionItem[]>({
      path: '/logistics/company-profile/versions',
    })
  },

  async createVersionDraft(): Promise<CompanyProfile> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/company-profile/versions',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
  },

  async activateVersion(versionId: string): Promise<CompanyProfile> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/company-profile/versions/${versionId}/activate`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
  },

  // Direcciones
  async listAddresses(): Promise<OrganizationAddress[]> {
    return apiRequest<OrganizationAddress[]>({
      path: '/logistics/company-profile/addresses',
    })
  },

  async createAddress(data: OrganizationAddressCreate): Promise<OrganizationAddress> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/company-profile/addresses',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async setPrimaryAddress(addressId: string): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `/logistics/company-profile/addresses/${addressId}/set-primary`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
  },

  // Contactos
  async listContacts(): Promise<OrganizationContact[]> {
    return apiRequest<OrganizationContact[]>({
      path: '/logistics/company-profile/contacts',
    })
  },

  async createContact(data: OrganizationContactCreate): Promise<OrganizationContact> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/company-profile/contacts',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Identidad Visual (Logotipos)
  async listAssets(): Promise<OrganizationAsset[]> {
    return apiRequest<OrganizationAsset[]>({
      path: '/logistics/company-profile/assets',
    })
  },

  async uploadLogo(file: File): Promise<OrganizationAsset> {
    const csrfToken = await getCsrfToken()
    const formData = new FormData()
    formData.append('file', file)
    return apiRequest({
      path: '/logistics/company-profile/assets/logo',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: formData,
    })
  },

  async activateAsset(assetId: string): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `/logistics/company-profile/assets/${assetId}/activate`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
  },

  // Firmantes Autorizados
  async listSigners(query?: ListQuery): Promise<PaginatedResponse<AuthorizedSigner>> {
    const params = new URLSearchParams()
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    if (query?.status) params.set('status', query.status)
    const qs = params.toString()
    const items = await apiRequest<AuthorizedSigner[]>({
      path: `/logistics/company-profile/signers${qs ? `?${qs}` : ''}`,
    })
    const page = query?.page ?? 1
    const pageSize = query?.page_size ?? Math.max(items.length, 1)
    const start = (page - 1) * pageSize
    return {
      items: items.slice(start, start + pageSize),
      page,
      page_size: pageSize,
      total: items.length,
      total_pages: Math.max(Math.ceil(items.length / pageSize), 1),
    }
  },

  async createSigner(data: AuthorizedSignerCreate): Promise<AuthorizedSigner> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/company-profile/signers',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async uploadSignerSignature(signerId: string, file: File): Promise<void> {
    const csrfToken = await getCsrfToken()
    const formData = new FormData()
    formData.append('signature', file)
    await apiRequest({
      path: `/logistics/company-profile/signers/${signerId}/signature`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: formData,
    })
  },

  async revokeSigner(signerId: string, reason: string): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `/logistics/company-profile/signers/${signerId}/revoke`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason },
    })
  },

  // Reglas de Numeración
  async listNumberingPolicies(): Promise<NumberingPolicy[]> {
    return apiRequest<NumberingPolicy[]>({
      path: '/logistics/company-profile/numbering-policies',
    })
  },

  async createNumberingPolicy(data: NumberingPolicyCreate): Promise<NumberingPolicy> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/company-profile/numbering-policies',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Vista Previa Documental (Logística - Fase 021)
  async getPreviewDocumentBlob(data: InstitutionalPreviewRequest): Promise<Blob> {
    const csrfToken = await getCsrfToken()
    const payload = {
      doc_type_code: data.doc_type_code,
      branch_id: data.branch_id || null,
      signer_id: data.signer_id || null,
      custom_data: data.custom_data ?? {},
    }

    const response = await fetch(`${API_ROOT}/logistics/company-profile/document-preview`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/pdf',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      let errorMessage = `Error ${response.status} al generar vista previa institucional`
      try {
        const errorJson = (await response.json()) as Record<string, unknown>
        if (typeof errorJson === 'object' && errorJson !== null) {
          if (typeof errorJson.detail === 'string') {
            errorMessage = errorJson.detail
          } else if (Array.isArray(errorJson.detail) && errorJson.detail.length > 0) {
            errorMessage = errorJson.detail
              .map((d: { msg?: string }) => d.msg ?? JSON.stringify(d))
              .join(', ')
          } else if (typeof errorJson.message === 'string') {
            errorMessage = errorJson.message
          } else if (
            errorJson.error &&
            typeof errorJson.error === 'object' &&
            typeof (errorJson.error as { message?: string }).message === 'string'
          ) {
            errorMessage = (errorJson.error as { message: string }).message
          }
        }
      } catch {
        // En caso de que no sea JSON
      }
      throw new Error(errorMessage)
    }

    const contentType = response.headers.get('content-type') ?? ''
    if (
      contentType &&
      !contentType.includes('application/pdf') &&
      !contentType.includes('application/octet-stream')
    ) {
      let detail = ''
      try {
        const body = (await response.json()) as { detail?: string; message?: string }
        detail = body?.detail ?? body?.message ?? JSON.stringify(body)
      } catch {
        // ignore
      }
      throw new Error(
        `Se esperaba un documento PDF pero el servidor respondió con ${contentType}. ${detail}`.trim(),
      )
    }

    const arrayBuffer = await response.arrayBuffer()
    return new Blob([arrayBuffer], { type: 'application/pdf' })
  },

  async getPreviewDocumentBlobUrl(data: InstitutionalPreviewRequest): Promise<string> {
    const blob = await this.getPreviewDocumentBlob(data)
    return URL.createObjectURL(blob)
  },
}
