import { apiRequest, getCsrfToken } from './api-client'
import type { PaginatedResponse } from '../types/logistics-resources'
import type {
  PurchaseRequisition,
  PurchaseRequisitionComment,
  PurchaseRequisitionCreate,
  PurchaseRequisitionDecision,
  PurchaseRequisitionListQuery,
  PurchaseRequisitionRevision,
  PurchaseRequisitionStats,
  PurchaseRequisitionSummary,
  PurchaseRequisitionUpdate,
  PurchaseRequisitionValidation,
} from '../types/purchase-requisitions'

const BASE = '/logistics/procurement/requisitions'

export const purchaseRequisitionsApi = {
  // ── Requisitions CRUD & Lists ─────────────────────────────────────────────

  async list(query?: PurchaseRequisitionListQuery): Promise<PaginatedResponse<PurchaseRequisitionSummary>> {
    const params = new URLSearchParams()
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    if (query?.search) params.set('search', query.search)
    if (query?.status) params.set('status', query.status)
    if (query?.priority) params.set('priority', query.priority)
    if (query?.cost_center_id) params.set('cost_center_id', query.cost_center_id)
    if (query?.applicant_user_id) params.set('applicant_user_id', query.applicant_user_id)
    if (query?.destination_warehouse_id) params.set('destination_warehouse_id', query.destination_warehouse_id)
    if (query?.product_id) params.set('product_id', query.product_id)
    if (query?.mine_only) params.set('mine_only', 'true')
    if (query?.pending_my_review) params.set('pending_my_review', 'true')
    if (query?.urgent_only) params.set('urgent_only', 'true')
    const qs = params.toString()
    return apiRequest({ path: `${BASE}${qs ? `?${qs}` : ''}` })
  },

  async get(id: string): Promise<PurchaseRequisition> {
    return apiRequest({ path: `${BASE}/${id}` })
  },

  async getStats(): Promise<PurchaseRequisitionStats> {
    try {
      // NOT_IN_CONTRACT_0.9.3: GET /logistics/procurement/requisitions/stats
      return await apiRequest({ path: `${BASE}/stats` })
    } catch {
      return {
        total_requisitions: 0,
        draft_count: 0,
        submitted_count: 0,
        under_review_count: 0,
        approved_count: 0,
        rejected_count: 0,
        returned_count: 0,
        urgent_count: 0,
        pending_my_review_count: 0,
      }
    }
  },

  async create(data: PurchaseRequisitionCreate): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async update(id: string, data: PurchaseRequisitionUpdate): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}`,
      method: 'PATCH',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // ── Validation & Submission ───────────────────────────────────────────────

  async validate(id: string): Promise<PurchaseRequisitionValidation> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}/validate`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {},
    })
  },

  async submit(id: string, idempotencyKey?: string): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    const headers: Record<string, string> = { 'X-CSRF-Token': csrfToken }
    if (idempotencyKey) headers['X-Idempotency-Key'] = idempotencyKey
    return apiRequest({
      path: `${BASE}/${id}/submit`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  // ── Approval Workflow ─────────────────────────────────────────────────────

  async startReview(id: string): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}/start-review`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {},
    })
  },

  async approve(id: string, comments: string, conditions?: string, idempotencyKey?: string): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    const headers: Record<string, string> = { 'X-CSRF-Token': csrfToken }
    if (idempotencyKey) headers['X-Idempotency-Key'] = idempotencyKey
    return apiRequest({
      path: `${BASE}/${id}/approve`,
      method: 'POST',
      headers,
      body: { comments, conditions },
    })
  },

  async reject(id: string, comments: string, reasonCode?: string): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}/reject`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { comments, reason_code: reasonCode },
    })
  },

  async returnForChanges(id: string, comments: string, lineNotes?: Record<string, string>): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}/return`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { comments, line_notes: lineNotes },
    })
  },

  async withdraw(id: string, reason: string): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}/withdraw`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason },
    })
  },

  async cancel(id: string, reason: string): Promise<PurchaseRequisition> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}/cancel`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason },
    })
  },

  // ── Revisions & Comparison ────────────────────────────────────────────────

  async listRevisions(id: string): Promise<PurchaseRequisitionRevision[]> {
    try {
      const res = await apiRequest<PurchaseRequisitionRevision[] | { items: PurchaseRequisitionRevision[] }>({
        path: `${BASE}/${id}/revisions`,
      })
      if (Array.isArray(res)) return res
      return res.items || []
    } catch {
      return []
    }
  },

  async getRevision(id: string, _revNum: number): Promise<PurchaseRequisition> {
    return this.get(id)
  },

  async compareRevisions(_id: string, _revA: number, _revB: number): Promise<{
    diffs: Array<{ field_name: string; field_label: string; value_a: string; value_b: string; change_type: 'ADDED' | 'REMOVED' | 'MODIFIED' }>
  }> {
    return { diffs: [] }
  },

  // ── Comments & History ────────────────────────────────────────────────────

  async listComments(id: string): Promise<PurchaseRequisitionComment[]> {
    try {
      const res = await apiRequest<PurchaseRequisitionComment[] | { items: PurchaseRequisitionComment[] }>({
        path: `${BASE}/${id}/comments`,
      })
      if (Array.isArray(res)) return res
      return res.items || []
    } catch {
      return []
    }
  },

  async addComment(id: string, content: string): Promise<PurchaseRequisitionComment> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${id}/comments`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { content },
    })
  },

  async getHistory(id: string): Promise<Array<{ id: string; action: string; description: string; user_name: string; created_at: string }>> {
    try {
      const res = await apiRequest<Array<{ id: string; action: string; description: string; user_name: string; created_at: string }> | { items: Array<{ id: string; action: string; description: string; user_name: string; created_at: string }> }>({
        path: `${BASE}/${id}/history`,
      })
      if (Array.isArray(res)) return res
      return res.items || []
    } catch {
      return []
    }
  },

  async listDecisions(_id: string): Promise<PurchaseRequisitionDecision[]> {
    return []
  },

}
