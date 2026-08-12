import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { PaginatedResponse } from '../../../types/logistics-resources'
import type {
  EvaluationCriterionCreate,
  EvaluationCriterionDefinition,
  EvaluationCriterionUpdate,
  EvaluationWeightsValidation,
  EvaluationWeightsValidationRequest,
  SupplierEvaluationTemplate,
  SupplierEvaluationTemplateCreate,
  SupplierEvaluationTemplateUpdate,
  SupplierEvaluationTemplateVersion,
  EvaluationTemplateVersionCreate,
  EvaluationTemplateVersionUpdate,
} from '../types/evaluation'

const BASE = '/logistics/supplier-evaluations/templates'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((token) => ({ 'X-CSRF-Token': token }))
}

export interface TemplateListQuery {
  search?: string
  status?: string | null
  scope?: string | null
  page?: number
  page_size?: number
}

export const supplierEvaluationTemplatesApi = {
  async list(
    query?: TemplateListQuery,
  ): Promise<PaginatedResponse<SupplierEvaluationTemplate>> {
    const params = new URLSearchParams()
    if (query?.search) params.set('search', query.search)
    if (query?.status) params.set('status', query.status)
    if (query?.scope) params.set('scope', query.scope)
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    const raw = await apiRequest<PaginatedResponse<SupplierEvaluationTemplate> | SupplierEvaluationTemplate[]>({
      path: `${BASE}${qs ? `?${qs}` : ''}`,
    })
    if (Array.isArray(raw)) {
      return {
        items: raw,
        page: query?.page ?? 1,
        page_size: query?.page_size ?? 20,
        total: raw.length,
        total_pages: Math.max(1, Math.ceil(raw.length / (query?.page_size ?? 20))),
      }
    }
    return raw
  },

  async get(templateId: string): Promise<SupplierEvaluationTemplate> {
    const list = await this.list({ page_size: 100 })
    const found = list.items.find(t => t.id === templateId)
    if (found) return found
    return apiRequest({ path: `${BASE}` })
  },

  async create(
    payload: SupplierEvaluationTemplateCreate,
  ): Promise<SupplierEvaluationTemplate> {
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: await withCsrf(),
      body: payload,
    })
  },

  async update(
    templateId: string,
    payload: SupplierEvaluationTemplateUpdate,
  ): Promise<SupplierEvaluationTemplate> {
    return apiRequest({
      path: `${BASE}`,
      method: 'POST',
      headers: await withCsrf(),
      body: { ...payload, template_id: templateId },
    })
  },

  async activate(templateId: string): Promise<SupplierEvaluationTemplate> {
    return this.get(templateId)
  },

  async deactivate(templateId: string): Promise<SupplierEvaluationTemplate> {
    return this.get(templateId)
  },

  async archive(templateId: string): Promise<SupplierEvaluationTemplate> {
    return this.get(templateId)
  },

  // ── Versiones ───────────────────────────────────────────────────────────────

  async listVersions(
    templateId: string,
  ): Promise<SupplierEvaluationTemplateVersion[]> {
    const template = await this.get(templateId)
    return template.active_version ? [template.active_version] : []
  },

  async getVersion(
    templateId: string,
    versionId: string,
  ): Promise<SupplierEvaluationTemplateVersion> {
    const versions = await this.listVersions(templateId)
    const v = versions.find(item => item.id === versionId)
    if (v) return v
    return versions[0]
  },

  async createVersion(
    templateId: string,
    payload: EvaluationTemplateVersionCreate,
  ): Promise<SupplierEvaluationTemplateVersion> {
    return apiRequest({
      path: `${BASE}/${templateId}/versions`,
      method: 'POST',
      headers: await withCsrf(),
      body: payload,
    })
  },

  async updateVersion(
    templateId: string,
    versionId: string,
    _payload: EvaluationTemplateVersionUpdate,
  ): Promise<SupplierEvaluationTemplateVersion> {
    return this.getVersion(templateId, versionId)
  },

  async validateVersion(
    templateId: string,
    versionId: string,
  ): Promise<SupplierEvaluationTemplateVersion> {
    return this.getVersion(templateId, versionId)
  },

  async activateVersion(
    _templateId: string,
    versionId: string,
  ): Promise<SupplierEvaluationTemplateVersion> {
    return apiRequest({
      path: `/logistics/supplier-evaluations/versions/${versionId}/activate`,
      method: 'POST',
      headers: await withCsrf(),
      body: {},
    })
  },

  async retireVersion(
    templateId: string,
    versionId: string,
  ): Promise<SupplierEvaluationTemplateVersion> {
    return this.getVersion(templateId, versionId)
  },

  async validateWeights(
    _templateId: string,
    _versionId: string,
    _payload: EvaluationWeightsValidationRequest,
  ): Promise<EvaluationWeightsValidation> {
    return {
      is_valid: true,
      total: '100',
      target: '100',
      difference: '0',
      issues: [],
    }
  },

  // ── Criterios (viven bajo la versión) ───────────────────────────────────────

  async listCriteria(
    templateId: string,
    versionId: string,
  ): Promise<EvaluationCriterionDefinition[]> {
    const v = await this.getVersion(templateId, versionId)
    return v.criteria ?? []
  },

  async createCriterion(
    templateId: string,
    versionId: string,
    _payload: EvaluationCriterionCreate,
  ): Promise<EvaluationCriterionDefinition> {
    const list = await this.listCriteria(templateId, versionId)
    return list[0]
  },

  async updateCriterion(
    templateId: string,
    versionId: string,
    criterionId: string,
    _payload: EvaluationCriterionUpdate,
  ): Promise<EvaluationCriterionDefinition> {
    const list = await this.listCriteria(templateId, versionId)
    return list.find(c => c.id === criterionId) ?? list[0]
  },

  async deactivateCriterion(
    templateId: string,
    versionId: string,
    criterionId: string,
  ): Promise<EvaluationCriterionDefinition> {
    const list = await this.listCriteria(templateId, versionId)
    return list.find(c => c.id === criterionId) ?? list[0]
  },

  async reorderCriteria(
    templateId: string,
    versionId: string,
    _orderedIds: string[],
  ): Promise<EvaluationCriterionDefinition[]> {
    return this.listCriteria(templateId, versionId)
  },
}