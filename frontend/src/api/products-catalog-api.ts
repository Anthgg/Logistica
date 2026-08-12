import { apiRequest, getCsrfToken } from './api-client'
import type { ListQuery, PaginatedResponse } from '../types/logistics-resources'
import type {
  Product,
  ProductBrand,
  ProductBrandCreate,
  ProductCategory,
  ProductCategoryCreate,
  ProductCreate,
  ProductHandlingCondition,
  ProductHistoryEvent,
  ProductIdentifier,
  ProductIdentifierCreate,
  ProductPhysicalProfile,
  ProductPhysicalProfileUpdate,
  ProductStorageCondition,
  ProductTrackingPolicy,
  ProductTrackingPolicyUpdate,
} from '../types/products-catalog'

interface BackendProduct {
  id: string
  sku: string
  name: string
  short_name: string | null
  description: string | null
  product_type: string
  category_id: string
  brand_id: string | null
  base_unit_code: string
  status: string
  row_version: number
  created_at: string
  updated_at: string
  category?: { name: string } | null
  brand?: { name: string } | null
  identifiers?: ProductIdentifier[]
  physical_profile?: Record<string, unknown> | null
  tracking_policy?: Record<string, unknown> | null
}

function normalizeProduct(product: BackendProduct): Product {
  const trackingType =
    typeof product.tracking_policy?.tracking_type === 'string'
      ? product.tracking_policy.tracking_type
      : 'NONE'
  return {
    id: product.id,
    sku: product.sku,
    name: product.name,
    short_name: product.short_name,
    description: product.description,
    product_type: product.product_type as Product['product_type'],
    category_id: product.category_id,
    category_name: product.category?.name,
    brand_id: product.brand_id,
    brand_name: product.brand?.name,
    base_unit: product.base_unit_code,
    status: product.status as Product['status'],
    active_version: product.row_version,
    primary_identifier_value:
      product.identifiers?.find((identifier) => identifier.is_primary)?.value ?? null,
    tracking_type: trackingType as Product['tracking_type'],
    requires_expiration:
      product.tracking_policy?.expiration_control === true,
    is_fragile: false,
    has_cold_chain: false,
    has_hazmat: false,
    is_high_value: false,
    created_at: product.created_at,
    updated_at: product.updated_at,
    capabilities: {
      can_view: true,
      can_create: false,
      can_update: false,
      can_activate: product.status === 'DRAFT',
      can_suspend: product.status === 'ACTIVE',
      can_discontinue: product.status === 'ACTIVE',
      can_archive: false,
      can_manage_identifiers: true,
      can_manage_tracking: true,
      can_manage_conditions: true,
      can_view_history: true,
      can_create_version: false,
      can_activate_version: false,
    },
  }
}

export const productsCatalogApi = {
  // Productos
  async list(query?: ListQuery): Promise<PaginatedResponse<Product>> {
    const params = new URLSearchParams()
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    if (query?.search) params.set('search', query.search)
    if (query?.status) params.set('status', query.status)
    const qs = params.toString()
    const response = await apiRequest<{
      items: BackendProduct[]
      total: number
      page: number
      page_size: number
    }>({
      path: `/logistics/products${qs ? `?${qs}` : ''}`,
    })
    return {
      ...response,
      total_pages: Math.max(Math.ceil(response.total / response.page_size), 1),
      items: response.items.map(normalizeProduct),
    }
  },

  async get(id: string): Promise<Product> {
    const response = await apiRequest<BackendProduct>({
      path: `/logistics/products/${id}`,
    })
    return normalizeProduct(response)
  },

  async create(data: ProductCreate): Promise<Product> {
    const csrfToken = await getCsrfToken()
    const response = await apiRequest<BackendProduct>({
      path: '/logistics/products',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {
        sku: data.sku,
        name: data.name,
        short_name: data.short_name || null,
        description: data.description || null,
        product_type: data.product_type,
        category_id: data.category_id,
        brand_id: data.brand_id || null,
        base_unit_code: data.base_unit,
      },
    })
    return normalizeProduct(response)
  },

  async update(id: string, _data: Partial<ProductCreate>): Promise<Product> {
    return this.get(id)
  },

  async activate(id: string): Promise<Product> {
    const csrfToken = await getCsrfToken()
    const res = await apiRequest<BackendProduct>({
      path: `/logistics/products/${id}/status`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { target_status: 'ACTIVE', reason: 'Activación desde ficha de producto.' },
    })
    return normalizeProduct(res)
  },

  async suspend(id: string, reason: string): Promise<Product> {
    const csrfToken = await getCsrfToken()
    const res = await apiRequest<BackendProduct>({
      path: `/logistics/products/${id}/status`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { target_status: 'SUSPENDED', reason },
    })
    return normalizeProduct(res)
  },

  async discontinue(id: string, reason: string): Promise<Product> {
    const csrfToken = await getCsrfToken()
    const res = await apiRequest<BackendProduct>({
      path: `/logistics/products/${id}/status`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { target_status: 'DISCONTINUED', reason },
    })
    return normalizeProduct(res)
  },

  // Categorías
  async listCategories(): Promise<ProductCategory[]> {
    return apiRequest<ProductCategory[]>({
      path: '/logistics/product-categories',
    })
  },

  async createCategory(data: ProductCategoryCreate): Promise<ProductCategory> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/product-categories',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Marcas
  async listBrands(): Promise<ProductBrand[]> {
    return apiRequest<ProductBrand[]>({
      path: '/logistics/product-brands',
    })
  },

  async createBrand(data: ProductBrandCreate): Promise<ProductBrand> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/product-brands',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Identificadores (Códigos de Barras)
  async listIdentifiers(productId: string): Promise<ProductIdentifier[]> {
    const response = await apiRequest<BackendProduct>({
      path: `/logistics/products/${productId}`,
    })
    return (response.identifiers ?? []).map((identifier) => ({
      ...identifier,
      is_active:
        (identifier as ProductIdentifier & { status?: string }).status !== 'INACTIVE',
    }))
  },

  async createIdentifier(productId: string, data: ProductIdentifierCreate): Promise<ProductIdentifier> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/products/${productId}/identifiers`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Perfil Físico
  async getPhysicalProfile(productId: string): Promise<ProductPhysicalProfile> {
    const product = await apiRequest<BackendProduct>({
      path: `/logistics/products/${productId}`,
    })
    const profile = product.physical_profile ?? {}
    return {
      product_id: productId,
      net_weight_kg: String(profile.net_weight_value ?? '0'),
      gross_weight_kg: String(profile.gross_weight_value ?? '0'),
      length_cm: String(profile.length_value ?? '0'),
      width_cm: String(profile.width_value ?? '0'),
      height_cm: String(profile.height_value ?? '0'),
      reported_volume_m3: String(profile.volume_value ?? '0'),
      calculated_volume_m3: String(profile.volume_value ?? '0'),
      measurement_source: String(profile.measurement_source ?? 'NOT_REPORTED'),
      verified_at: null,
    }
  },

  async updatePhysicalProfile(productId: string, data: ProductPhysicalProfileUpdate): Promise<ProductPhysicalProfile> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/products/${productId}/physical-profile`,
      method: 'PUT',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Trazabilidad
  async getTrackingPolicy(productId: string): Promise<ProductTrackingPolicy> {
    const product = await apiRequest<BackendProduct>({
      path: `/logistics/products/${productId}`,
    })
    const policy = product.tracking_policy ?? {}
    return {
      product_id: productId,
      tracking_type: String(policy.tracking_type ?? 'NONE') as ProductTrackingPolicy['tracking_type'],
      requires_expiration: policy.expiration_control === true,
      requires_manufacturing_date: policy.manufacturing_date_control === true,
      total_shelf_life_days:
        typeof policy.total_shelf_life_days === 'number'
          ? policy.total_shelf_life_days
          : null,
      min_remaining_shelf_life_days:
        typeof policy.minimum_shelf_life_days === 'number'
          ? policy.minimum_shelf_life_days
          : null,
      allow_mixed_lots: false,
      require_supplier_lot: false,
    }
  },

  async updateTrackingPolicy(productId: string, data: ProductTrackingPolicyUpdate): Promise<ProductTrackingPolicy> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/products/${productId}/tracking-policy`,
      method: 'PUT',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Condiciones de Almacenamiento
  async listStorageConditions(_productId: string): Promise<ProductStorageCondition[]> {
    return []
  },

  // Condiciones de Manipulación
  async listHandlingConditions(_productId: string): Promise<ProductHandlingCondition[]> {
    return []
  },

  // Historial
  async getHistory(productId: string): Promise<ProductHistoryEvent[]> {
    try {
      const res = await apiRequest<ProductHistoryEvent[] | { items: ProductHistoryEvent[] }>({
        path: `/logistics/products/${productId}/versions`,
      })
      if (Array.isArray(res)) return res
      return res.items || []
    } catch {
      return []
    }
  },
}
