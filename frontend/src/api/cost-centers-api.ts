import { apiRequest, getCsrfToken } from './api-client'
import type {
  CostCenter,
  CostCenterCreate,
  CostCenterStatus,
  CostCenterUpdate,
} from '../types/purchase-requisitions'

const BASE = '/logistics/cost-centers'

export interface CostCenterListQuery {
  status?: CostCenterStatus | ''
  branch_id?: string | null
  skip?: number
  limit?: number
}

export const costCentersApi = {
  async list(query?: CostCenterListQuery): Promise<CostCenter[]> {
    const params = new URLSearchParams()
    if (query?.status) params.set('status', query.status)
    if (query?.branch_id) params.set('branch_id', query.branch_id)
    if (query?.skip !== undefined) params.set('skip', String(query.skip))
    if (query?.limit !== undefined) params.set('limit', String(query.limit))
    const queryString = params.toString()
    return apiRequest({ path: `${BASE}${queryString ? `?${queryString}` : ''}` })
  },

  async create(data: CostCenterCreate): Promise<CostCenter> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async update(id: string, data: CostCenterUpdate): Promise<CostCenter> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}`,
      method: 'PATCH',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async activate(id: string): Promise<CostCenter> {
    return this.transition(id, 'activate')
  },

  async deactivate(id: string): Promise<CostCenter> {
    return this.transition(id, 'deactivate')
  },

  async archive(id: string): Promise<CostCenter> {
    return this.transition(id, 'archive')
  },

  async transition(id: string, action: 'activate' | 'deactivate' | 'archive'): Promise<CostCenter> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}/${action}`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {},
    })
  },
}
