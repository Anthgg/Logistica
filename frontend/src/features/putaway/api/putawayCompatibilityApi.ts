import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/putaway/compatibility-rules'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export interface CompatibilityRule {
  rule_id: string
  rule_name: string
  description?: string
  rule_type: 'product_category' | 'temperature' | 'hazmat' | 'lot_group' | 'custom'
  conditions: Record<string, unknown>
  action: 'allow' | 'block' | 'restrict'
  priority: number
  is_active: boolean
}

export interface CompatibilityEvaluation {
  is_compatible: boolean
  incompatibilities: { rule_id: string; reason: string; severity: string }[]
  effective_rules: CompatibilityRule[]
}

export const putawayCompatibilityApi = {
  async listRules(warehouseId?: string): Promise<CompatibilityRule[]> {
    const qs = warehouseId ? `?warehouse_id=${warehouseId}` : ''
    return apiRequest({ path: `${BASE}${qs}`, method: 'GET' })
  },

  async createRule(data: Omit<CompatibilityRule, 'rule_id'>): Promise<CompatibilityRule> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async evaluate(productId: string, locationId: string): Promise<CompatibilityEvaluation> {
    return apiRequest({
      path: `/logistics/putaway/compatibility/evaluate?product_id=${productId}&location_id=${locationId}`,
      method: 'GET',
    })
  },
}
