import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/putaway/tasks'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function buildQuery(params?: Record<string, unknown>): string {
  if (!params) return ''
  const entries: [string, string][] = []
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue
    if (Array.isArray(v)) {
      for (const item of v) entries.push([k, String(item)])
    } else {
      entries.push([k, String(v)])
    }
  }
  return entries.length ? `?${new URLSearchParams(entries).toString()}` : ''
}

export const putawayTasksApi = {
  /** GET /putaway/tasks */
  async listTasks(params?: Record<string, unknown>): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}${buildQuery(params)}`, method: 'GET' })
  },

  /** POST /putaway/tasks */
  async createTask(data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/tasks/{task_id} */
  async getTask(taskId: string): Promise<unknown> {
    return apiRequest({ path: `${BASE}/${taskId}`, method: 'GET' })
  },

  /** POST /putaway/tasks/{task_id}/assign */
  async assignTask(data: { task_id: string; user_id: string }): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${data.task_id}/assign`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { user_id: data.user_id },
    })
  },

  /** POST /putaway/tasks/{task_id}/start */
  async startTask(data: { task_id: string }): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${data.task_id}/start`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /putaway/tasks/{task_id}/complete */
  async completeTask(data: { task_id: string } & Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    const { task_id, ...body } = data
    return apiRequest({
      path: `${BASE}/${task_id}/complete`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body,
    })
  },

  /** GET /putaway/tasks/{task_id}/destinations */
  async getDestinations(taskId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${taskId}/destinations`, method: 'GET' })
  },

  /** GET /putaway/tasks/{task_id}/assignments */
  async getAssignments(taskId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${taskId}/assignments`, method: 'GET' })
  },

  /** POST /putaway/tasks/{task_id}/sessions */
  async createSession(taskId: string, data: Record<string, unknown> = {}): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${taskId}/sessions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /putaway/tasks/{task_id}/placements */
  async createPlacement(taskId: string, data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${taskId}/placements`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/tasks/{task_id}/placements */
  async getPlacements(taskId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${taskId}/placements`, method: 'GET' })
  },

  /** POST /putaway/tasks/{task_id}/overrides */
  async createOverride(taskId: string, data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${taskId}/overrides`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/tasks/{task_id}/overrides */
  async getOverrides(taskId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${taskId}/overrides`, method: 'GET' })
  },

  /** POST /putaway/tasks/{task_id}/exceptions */
  async createException(taskId: string, data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${taskId}/exceptions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/tasks/{task_id}/exceptions */
  async getExceptions(taskId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${taskId}/exceptions`, method: 'GET' })
  },

  /** POST /putaway/tasks/{task_id}/pauses */
  async createPause(taskId: string, data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${taskId}/pauses`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/tasks/{task_id}/pauses */
  async getPauses(taskId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${taskId}/pauses`, method: 'GET' })
  },

  /** POST /putaway/tasks/{task_id}/resume */
  async resumeTask(taskId: string): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${taskId}/resume`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  // Legacy helpers
  async divertTask(data: { task_id: string; diversion_reason: string }): Promise<unknown> {
    return this.createOverride(data.task_id, { reason: data.diversion_reason })
  },
  async cancelTask(taskId: string): Promise<unknown> {
    return this.createException(taskId, { type: 'cancelled' })
  },
  async updatePriority(data: { task_id: string; priority: string }): Promise<unknown> {
    return this.getTask(data.task_id)
  },
  async bulkAssign(data: { task_ids: string[]; user_id: string }): Promise<unknown[]> {
    const results = await Promise.all(
      data.task_ids.map((task_id) => this.assignTask({ task_id, user_id: data.user_id })),
    )
    return results
  },
  async bulkComplete(data: { completions: Array<{ task_id: string } & Record<string, unknown>> }): Promise<unknown[]> {
    const results = await Promise.all(
      data.completions.map((c) => this.completeTask(c)),
    )
    return results
  },
}
