import { type Page } from '@playwright/test'

export interface MockPermissionsOptions {
  permissions?: string[]
  sensitivePermissions?: string[]
  stepUpPermissions?: string[]
  roles?: Array<{
    role_code: string
    role_name: string
    scope_type: string
    organization_id: string | null
    branch_id: string | null
    warehouse_id: string | null
    expires_at: string | null
  }>
}

export const defaultUser = {
  id: '0f02a6e1-b9ca-4e4a-b85d-5fd469943a78',
  email: 'admin@andeslog.test',
  full_name: 'Admin de Prueba',
  role: 'admin',
  is_active: true,
  is_verified: true,
  created_at: '2026-01-10T10:00:00Z',
}

export const defaultSession = {
  id: '481f1eb4-5eb0-43f8-b5ac-5e44491730d2',
  authentication_level: 'traditional',
  created_at: '2026-07-20T10:00:00Z',
  last_activity_at: '2026-07-23T10:00:00Z',
  expires_at: '2026-08-20T10:00:00Z',
  device_id: null,
}

export const defaultCatalog = {
  locale: 'es',
  supported_locales: ['es', 'en', 'pt'],
  translations: {
    common: { admin: 'Administrador', operator: 'Operador' },
    status: {
      active: 'Activo',
      inactive: 'Inactivo',
      pending_pickup: 'Por recoger',
      delivered: 'Entregado',
    },
    priority: { low: 'Baja', normal: 'Normal', high: 'Alta', urgent: 'Urgente' },
    event: {},
    resource: { system: 'sistema' },
    risk: {
      low: 'Riesgo bajo',
      medium: 'Riesgo moderado',
      high: 'Riesgo alto',
      critical: 'Riesgo crítico',
      unknown: 'Riesgo sin determinar',
    },
    auth_level: {
      traditional: 'Sesión tradicional',
      continuously_verified: 'Identidad verificada',
      verification_required: 'Reverificación requerida',
      restricted: 'Sesión restringida',
      terminated: 'Sesión finalizada',
      password: 'Contraseña',
    },
    continuous_auth_status: {
      active: 'Activa',
      available: 'Disponible',
      pending: 'Pendiente',
      unavailable: 'No disponible',
      failed: 'Error temporal',
      degraded: 'Disponibilidad limitada',
    },
    action: {
      maintain_session: 'Mantener sesión',
      increase_monitoring: 'Incrementar supervisión',
      request_reverification: 'Solicitar reverificación',
      restrict_sensitive_operations: 'Restringir operaciones sensibles',
      terminate_session: 'Finalizar sesión',
      none: 'Sin acción adicional',
    },
  },
}

const DEFAULT_PERMISSIONS = [
  'logistics.organizations.read',
  'logistics.organizations.create',
  'logistics.organizations.update',
  'logistics.organizations.change_status',
  'logistics.branches.read',
  'logistics.branches.create',
  'logistics.branches.update',
  'logistics.branches.change_status',
  'logistics.warehouses.read',
  'logistics.warehouses.create',
  'logistics.warehouses.update',
  'logistics.warehouses.change_status',
  'logistics.warehouses.set_default',
  'logistics.roles.read',
  'logistics.role_assignments.read',
  'logistics.role_assignments.create',
  'logistics.role_assignments.update',
  'logistics.role_assignments.revoke',
  'logistics.permissions.read',
  'logistics.audit.read',
  'logistics.documents.read',
  'logistics.documents.download',
  'logistics.documents.export',
  'logistics.documents.cancel',
  'logistics.documents.reprint',
]

export function buildPermissionsResponse(
  options: MockPermissionsOptions = {},
) {
  return {
    success: true,
    catalog_version: '2026.07.26',
    user_id: defaultUser.id,
    permissions: options.permissions ?? DEFAULT_PERMISSIONS,
    sensitive_permissions: options.sensitivePermissions ?? [
      'logistics.documents.cancel',
      'logistics.documents.reprint',
      'logistics.role_assignments.revoke',
    ],
    step_up_permissions: options.stepUpPermissions ?? [
      'logistics.role_assignments.revoke',
    ],
    roles: options.roles ?? [
      {
        role_code: 'LOGISTICS_ADMIN',
        role_name: 'Administrador logístico global',
        scope_type: 'GLOBAL',
        organization_id: null,
        branch_id: null,
        warehouse_id: null,
        expires_at: null,
      },
    ],
  }
}

export function buildEmptyPermissionsResponse(): ReturnType<
  typeof buildPermissionsResponse
> {
  return {
    success: true,
    catalog_version: '2026.07.26',
    user_id: defaultUser.id,
    permissions: [],
    sensitive_permissions: [],
    step_up_permissions: [],
    roles: [],
  }
}

export function buildLogisticsMeResponse(options: {
  enabled?: boolean
  roles?: string[]
  permissions?: string[]
  sensitivePermissions?: string[]
  stepUpPermissions?: string[]
  organizations?: string[]
  branches?: string[]
  warehouses?: string[]
  defaultOrganizationId?: string | null
  defaultBranchId?: string | null
  defaultWarehouseId?: string | null
} = {}) {
  return {
    success: true,
    user: {
      id: defaultUser.id,
      display_name: defaultUser.full_name,
      email: defaultUser.email,
      platform_role: defaultUser.role,
      is_active: true,
    },
    session: {
      id: defaultSession.id,
      device_id: null,
      expires_at: defaultSession.expires_at,
      authentication_level: 'traditional',
      risk_score: null,
    },
    logistics: {
      enabled: options.enabled ?? true,
      roles: options.roles ?? ['LOGISTICS_ADMIN'],
      permissions: options.permissions ?? DEFAULT_PERMISSIONS,
      sensitive_permissions: options.sensitivePermissions ?? [],
      step_up_permissions: options.stepUpPermissions ?? [],
      organizations: options.organizations ?? ['org-1', 'org-2'],
      branches: options.branches ?? ['branch-1'],
      warehouses: options.warehouses ?? ['wh-1'],
      default_organization_id: options.defaultOrganizationId ?? 'org-1',
      default_branch_id: options.defaultBranchId ?? 'branch-1',
      default_warehouse_id: options.defaultWarehouseId ?? 'wh-1',
    },
  }
}

export function buildDisabledLogisticsMeResponse() {
  return buildLogisticsMeResponse({
    enabled: false,
    roles: [],
    permissions: [],
    organizations: [],
    branches: [],
    warehouses: [],
    defaultOrganizationId: null,
    defaultBranchId: null,
    defaultWarehouseId: null,
  })
}

export async function installApiMocks(
  page: Page,
  permissionsOptions: MockPermissionsOptions = {},
  logisticsMeOptions: Parameters<typeof buildLogisticsMeResponse>[0] = {},
  overrides: Record<string, unknown> = {},
): Promise<void> {
  await page.addInitScript(() => {
    window.__mswReady = false
  })

  const meOptions: Parameters<typeof buildLogisticsMeResponse>[0] = {}
  if (logisticsMeOptions.permissions !== undefined)
    meOptions.permissions = logisticsMeOptions.permissions
  else if (permissionsOptions.permissions !== undefined)
    meOptions.permissions = permissionsOptions.permissions
  else meOptions.permissions = DEFAULT_PERMISSIONS

  if (logisticsMeOptions.sensitivePermissions !== undefined)
    meOptions.sensitivePermissions = logisticsMeOptions.sensitivePermissions
  else if (permissionsOptions.sensitivePermissions !== undefined)
    meOptions.sensitivePermissions = permissionsOptions.sensitivePermissions

  if (logisticsMeOptions.stepUpPermissions !== undefined)
    meOptions.stepUpPermissions = logisticsMeOptions.stepUpPermissions
  else if (permissionsOptions.stepUpPermissions !== undefined)
    meOptions.stepUpPermissions = permissionsOptions.stepUpPermissions

  meOptions.enabled = logisticsMeOptions.enabled
  meOptions.roles = logisticsMeOptions.roles
  meOptions.organizations = logisticsMeOptions.organizations
  meOptions.branches = logisticsMeOptions.branches
  meOptions.warehouses = logisticsMeOptions.warehouses
  meOptions.defaultOrganizationId = logisticsMeOptions.defaultOrganizationId
  meOptions.defaultBranchId = logisticsMeOptions.defaultBranchId
  meOptions.defaultWarehouseId = logisticsMeOptions.defaultWarehouseId

  await page.route('**/api/health', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok', database: { status: 'connected' } }),
    }),
  )

  await page.route('**/api/auth/csrf', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrf_token: 'test-csrf-token' }),
    }),
  )

  await page.route('**/api/i18n/catalog', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(defaultCatalog),
    }),
  )

  await page.route('**/api/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'ok',
        user: defaultUser,
        session: defaultSession,
      }),
    }),
  )

  await page.route('**/api/logistics/me/permissions', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildPermissionsResponse(permissionsOptions)),
    }),
  )

  await page.route('**/api/logistics/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildLogisticsMeResponse(meOptions)),
    }),
  )

  await page.route('**/api/logistics/me/context', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Contexto actualizado',
        context: buildLogisticsMeResponse(meOptions).logistics,
      }),
    }),
  )

  await page.route('**/api/auth/sessions', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [defaultSession] }),
    }),
  )

  await page.route('**/api/continuous-auth/status', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        risk_level: 'low',
        authentication_level: 'traditional',
        recommended_action: 'allow',
        applied_action: 'allow',
        components: [],
        score: 0.95,
        updated_at: new Date().toISOString(),
      }),
    }),
  )

  await page.route('**/api/dashboard/summary', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_shipments: 0,
        pending_shipments: 0,
        in_transit_shipments: 0,
        delivered_shipments: 0,
        delayed_shipments: 0,
        open_incidents: 0,
        critical_incidents: 0,
        low_stock_items: 0,
        routes_today: 0,
        deliveries_today: 0,
        recent_shipments: [],
        recent_activity: [],
        shipments_by_status: {},
      }),
    }),
  )

  await page.route(/\/api\/warehouses(?:[/?#]|$)/, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'wh-1',
            code: 'WH-001',
            name: 'Almacén Central',
            address: 'Av. Principal 123',
            district: 'Lima',
            province: 'Lima',
            department: 'Lima',
            capacity: '5000',
            is_active: true,
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      }),
    }),
  )

  await page.route('**/api/logistics/organizations', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'org-1',
            code: 'ORG-001',
            name: 'Organización Principal',
            status: 'active',
            country_code: 'PE',
            timezone: 'America/Lima',
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      }),
    }),
  )

  await page.route('**/api/logistics/organizations/*/branches**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'branch-1',
            organization_id: 'org-1',
            code: 'BR-001',
            name: 'Sede Central',
            status: 'active',
            timezone: 'America/Lima',
            address_text: 'Av. Principal 123',
            latitude: null,
            longitude: null,
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      }),
    }),
  )

  await page.route('**/api/logistics/roles', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'role-1',
            code: 'LOGISTICS_ADMIN',
            name: 'Administrador logístico',
            description: 'Acceso total al módulo logístico',
            role_type: 'system',
            is_system: true,
            status: 'active',
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      }),
    }),
  )

  await page.route('**/api/logistics/role-assignments', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'asg-1',
            user_id: 'user-1',
            role_id: 'role-1',
            scope_type: 'GLOBAL',
            organization_id: null,
            branch_id: null,
            warehouse_id: null,
            status: 'active',
            starts_at: null,
            ends_at: null,
            assigned_by: null,
            assigned_at: '2026-01-01T00:00:00Z',
            revoked_by: null,
            revoked_at: null,
            revocation_reason: null,
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      }),
    }),
  )

  await page.route('**/api/logistics/permissions', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'perm-1',
          code: 'logistics.warehouses.read',
          resource: 'warehouses',
          action: 'read',
          name: 'Ver almacenes',
          description: 'Permiso de lectura sobre almacenes',
          category: 'warehouses',
          risk_level: 'low',
          is_sensitive: false,
          requires_reason: false,
          requires_step_up: false,
          is_system: true,
          status: 'active',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ]),
    }),
  )

  await page.route('**/api/logistics/audit-events', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'evt-1',
            event_code: 'LOGISTICS_ACCESS_GRANTED',
            event_category: 'access',
            actor_user_id: 'user-1',
            actor_display_name_snapshot: 'Admin de Prueba',
            action: 'access',
            result: 'success',
            severity: 'low',
            resource_type: 'warehouse',
            resource_id: 'wh-1',
            organization_id: 'org-1',
            branch_id: null,
            warehouse_id: null,
            occurred_at: '2026-07-26T10:00:00Z',
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      }),
    }),
  )

  await page.route('**/api/logistics/documents', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'doc-1',
            code: 'DOC-001',
            document_type: 'guide',
            status: 'active',
            created_at: '2026-07-26T10:00:00Z',
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      }),
    }),
  )

  for (const [urlPattern, response] of Object.entries(overrides)) {
    await page.route(urlPattern, (route) =>
      route.fulfill({
        status: response.status ?? 200,
        contentType: 'application/json',
        body: JSON.stringify(response.body),
      }),
    )
  }
}

export async function installUnauthorizedMocks(page: Page): Promise<void> {
  await page.route('**/api/health', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok', database: { status: 'connected' } }),
    }),
  )

  await page.route('**/api/auth/csrf', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrf_token: 'test-csrf-token' }),
    }),
  )

  await page.route('**/api/i18n/catalog', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(defaultCatalog),
    }),
  )

  await page.route('**/api/auth/me', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        error: { code: 'SESSION_REQUIRED', message: 'Inicia sesión.' },
      }),
    }),
  )

  await page.route('**/api/auth/refresh', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        error: { code: 'SESSION_REQUIRED', message: 'Sin sesión.' },
      }),
    }),
  )
}
