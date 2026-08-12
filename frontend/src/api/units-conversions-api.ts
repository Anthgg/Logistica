import { apiRequest, getCsrfToken } from './api-client'
import type { ListQuery, PaginatedResponse } from '../types/logistics-resources'
import type {
  ConversionEvaluationRequest,
  ConversionEvaluationResponse,
  ProductPackagingDefinition,
  ProductUnitConfiguration,
  QuantityDecompositionResult,
  UnitConversionRule,
  UnitConversionRuleCreate,
  UnitOfMeasure,
  UnitOfMeasureCreate,
} from '../types/units-conversions'

export const unitsConversionsApi = {
  // Catálogo de Unidades
  async listUnits(query?: ListQuery): Promise<PaginatedResponse<UnitOfMeasure>> {
    const params = new URLSearchParams()
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    if (query?.search) params.set('search', query.search)
    if (query?.status) params.set('status', query.status)
    const qs = params.toString()
    const response = await apiRequest<Array<{
      id: string
      code: string
      name: string
      plural_name: string | null
      symbol: string
      dimension_id: string
      unit_scope: string
      status: string
      decimal_precision: number
      integer_only: boolean
      is_canonical: boolean
      system_defined: boolean
      created_at: string
    }>>({
      path: `/logistics/units${qs ? `?${qs}` : ''}`,
    })
    const page = query?.page ?? 1
    const pageSize = query?.page_size ?? Math.max(response.length, 1)
    const items = response.map((unit) => ({
      id: unit.id,
      code: unit.code,
      name: unit.name,
      plural_name: unit.plural_name,
      symbol: unit.symbol,
      dimension: unit.dimension_id as UnitOfMeasure['dimension'],
      scope: unit.unit_scope as UnitOfMeasure['scope'],
      status: unit.status as UnitOfMeasure['status'],
      decimal_precision: unit.decimal_precision,
      minimum_increment: '0',
      is_integer_only: unit.integer_only,
      is_canonical: unit.is_canonical,
      is_system_protected: unit.system_defined,
      created_at: unit.created_at,
      updated_at: unit.created_at,
    }))
    const start = (page - 1) * pageSize
    return {
      items: items.slice(start, start + pageSize),
      page,
      page_size: pageSize,
      total: items.length,
      total_pages: Math.max(Math.ceil(items.length / pageSize), 1),
    }
  },

  async createUnit(data: UnitOfMeasureCreate): Promise<UnitOfMeasure> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/units',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Reglas de Conversión
  async listConversionRules(query?: ListQuery): Promise<PaginatedResponse<UnitConversionRule>> {
    const page = query?.page ?? 1
    const pageSize = query?.page_size ?? 20
    return {
      items: [],
      page,
      page_size: pageSize,
      total: 0,
      total_pages: 1,
    }
  },

  async createConversionRule(data: UnitConversionRuleCreate): Promise<UnitConversionRule> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/unit-conversion-rules',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Motor Backend de Simulación (Cero operaciones en React)
  async evaluateConversion(req: ConversionEvaluationRequest): Promise<ConversionEvaluationResponse> {
    const csrfToken = await getCsrfToken()
    const response = await apiRequest<{
      input_quantity: string
      exact_result: string
      rounded_result: string
      target_unit: string
      effective_factor: string
      residual: string
      conversion_path: ConversionEvaluationResponse['path_steps']
    }>({
      path: '/logistics/unit-conversions/evaluate',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: req,
    })
    return {
      input_quantity: response.input_quantity,
      exact_result: response.exact_result,
      rounded_result: response.rounded_result,
      target_unit_code: response.target_unit,
      effective_factor: response.effective_factor,
      residual_quantity: response.residual,
      is_exact: response.residual === '0',
      path_steps: response.conversion_path,
      evaluated_at: new Date().toISOString(),
    }
  },

  async decomposeQuantity(productId: string, quantity: string): Promise<QuantityDecompositionResult> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/products/${productId}/unit-conversions/decompose`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { quantity },
    })
  },

  // Unidades y Empaques por Producto
  async getProductUnitConfiguration(productId: string): Promise<ProductUnitConfiguration> {
    return apiRequest({
      path: `/logistics/products/${productId}/unit-configuration`,
    })
  },

  async listProductPackaging(productId: string): Promise<ProductPackagingDefinition[]> {
    void productId
    return []
  },
}
