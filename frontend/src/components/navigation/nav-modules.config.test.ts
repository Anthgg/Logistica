import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import {
  ALL_NAVIGATION_MODULES,
  DEFAULT_PREFERENCES,
  NAVIGATION_GROUPS,
  groupNavigationModules,
  matchesNavigationQuery,
  resolveActiveModuleId,
  type NavigationModule,
} from './nav-modules.config'
import { LOGISTICS_PERMISSIONS } from '../../features/logistics-permissions/logistics-permissions-map'
import { extractRouteGuards } from '../../../scripts/extract-route-guards.mjs'

// ── Fuente de verdad del router ──────────────────────────────────────────────

const ROUTER_SOURCE = readFileSync('src/router/AppRouter.tsx', 'utf8')
const ROUTE_ROWS = extractRouteGuards(ROUTER_SOURCE)
const ROUTE_BY_PATH = new Map(ROUTE_ROWS.map((row) => [row.path, row]))

const ALL_PERMISSION_STRINGS = new Set(
  Object.values(LOGISTICS_PERMISSIONS).flatMap((group) =>
    Object.values(group as Record<string, string>),
  ),
)

function resolveGuardStrings(path: string): string[] {
  const row = ROUTE_BY_PATH.get(path)
  if (!row) return []
  return row.guards.map((key) => {
    if (key.startsWith('literal:')) return key.slice('literal:'.length)
    const [namespace, action] = key.split('.')
    const group = (LOGISTICS_PERMISSIONS as unknown as Record<string, Record<string, string>>)[namespace]
    return group?.[action] ?? `DESCONOCIDO:${key}`
  })
}

function navPermissions(module: NavigationModule): string[] {
  return [
    ...(module.permission ? [module.permission] : []),
    ...(module.anyOfPermissions ?? []),
  ]
}

/**
 * Módulos cuyo permiso de navegación es deliberadamente MÁS estricto que el
 * guard de la ruta: el botón se muestra a menos gente de la que puede entrar
 * por URL, lo cual es seguro. El caso peligroso (nav más laxo que la ruta)
 * nunca se permite.
 */
const STRICTER_THAN_ROUTE: Record<string, string> = {
  requisition_review_inbox:
    'La bandeja solo tiene sentido para quien revisa; la ruta permite entrar con read.',
}

// ── Agrupación ───────────────────────────────────────────────────────────────

describe('groupNavigationModules', () => {
  it('unifica recepción, compras y calidad sin perder rutas', () => {
    const relevantIds = new Set([
      'gate_control_dashboard',
      'inbound_docks_settings',
      'inbound_docks_queue',
      'inbound_docks_board',
      'reception_differences',
      'quality_inspection_plans',
      'quality_quarantine',
      'purchase_orders',
      'purchase_requisitions',
      'requisition_review_inbox',
      'procurement_approval_inbox',
      'procurement_approval_policies',
    ])
    const modules = ALL_NAVIGATION_MODULES.filter((module) => relevantIds.has(module.id))
    const items = groupNavigationModules(modules)

    expect(items).toHaveLength(3)
    expect(items.map((item) => item.type === 'group' && item.group.id)).toEqual([
      'inbound',
      'quality',
      'purchasing',
    ])
    expect(
      items.flatMap((item) => (item.type === 'group' ? item.modules : [item.module])),
    ).toHaveLength(modules.length)
  })

  it('mantiene plano un grupo cuando solo queda una ruta visible', () => {
    const plan = ALL_NAVIGATION_MODULES.find(
      (module) => module.id === 'quality_inspection_plans',
    )

    expect(plan).toBeDefined()
    expect(groupNavigationModules([plan!])).toEqual([
      { type: 'module', module: plan },
    ])
  })

  it('no emite un grupo vacío cuando ningún hijo es visible', () => {
    const soloSueltos = ALL_NAVIGATION_MODULES.filter((module) => !module.navigationGroup)
    const items = groupNavigationModules(soloSueltos)

    expect(items.every((item) => item.type === 'module')).toBe(true)
    expect(items).toHaveLength(soloSueltos.length)
  })

  it('muestra el grupo cuando hay al menos dos hijos permitidos', () => {
    const permitidos = ALL_NAVIGATION_MODULES.filter((module) =>
      ['drivers', 'driver_alerts'].includes(module.id),
    )
    const items = groupNavigationModules(permitidos)

    expect(items).toHaveLength(1)
    expect(items[0].type === 'group' && items[0].group.id).toBe('drivers')
  })

  it('reduce la barra completa a un puñado de botones', () => {
    const items = groupNavigationModules(ALL_NAVIGATION_MODULES)

    expect(items.length).toBeLessThan(20)
    expect(
      items.flatMap((item) => (item.type === 'group' ? item.modules : [item.module])),
    ).toHaveLength(ALL_NAVIGATION_MODULES.length)
  })

  it('ningún grupo supera el límite de diseño de 7 opciones', () => {
    for (const item of groupNavigationModules(ALL_NAVIGATION_MODULES)) {
      if (item.type !== 'group') continue
      expect(
        item.modules.length,
        `El grupo ${item.group.label} necesita sub-secciones internas`,
      ).toBeLessThanOrEqual(7)
    }
  })
})

// ── Catálogo de módulos ──────────────────────────────────────────────────────

describe('catálogo de módulos', () => {
  it('no repite rutas entre botones', () => {
    const routes = ALL_NAVIGATION_MODULES.map((module) => module.route)
    expect(new Set(routes).size).toBe(routes.length)
  })

  it('no repite ids entre módulos', () => {
    const ids = ALL_NAVIGATION_MODULES.map((module) => module.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('ningún botón apunta a una ruta que solo redirige a otro botón', () => {
    const navRoutes = new Set(ALL_NAVIGATION_MODULES.map((module) => module.route))
    const redirects = [
      ...ROUTER_SOURCE.matchAll(/path="([^"]+)"\s+element=\{<Navigate to="([^"]+)"/g),
    ]

    for (const [, from, to] of redirects) {
      const duplicated = navRoutes.has(from) && navRoutes.has(to)
      expect(duplicated, `${from} y ${to} serían dos botones para la misma pantalla`).toBe(false)
    }
  })

  it('cada módulo agrupado apunta a un grupo declarado', () => {
    for (const module of ALL_NAVIGATION_MODULES) {
      if (!module.navigationGroup) continue
      expect(NAVIGATION_GROUPS[module.navigationGroup]).toBeDefined()
    }
  })

  it('todos los grupos declarados se usan y tienen orden único', () => {
    const usados = new Set(
      ALL_NAVIGATION_MODULES.map((module) => module.navigationGroup).filter(Boolean),
    )
    const grupos = Object.values(NAVIGATION_GROUPS)

    for (const group of grupos) {
      expect(usados.has(group.id), `El grupo ${group.id} no tiene módulos`).toBe(true)
      expect(group.ariaLabel.length).toBeGreaterThan(0)
    }
    const orders = grupos.map((group) => group.order)
    expect(new Set(orders).size).toBe(orders.length)
  })

  it('todos los módulos tienen descripción funcional, no la ruta cruda', () => {
    for (const module of ALL_NAVIGATION_MODULES) {
      expect(module.description, `${module.id} sin descripción`).toBeTruthy()
      expect(module.description).not.toContain('/')
      expect(module.description?.toLowerCase()).not.toBe(module.label.toLowerCase())
    }
  })
})

// ── Iconos ───────────────────────────────────────────────────────────────────

describe('iconos', () => {
  const ICON_SOURCE = readFileSync('src/components/common/LogisticsIcon.tsx', 'utf8')
  const declared = new Set(
    [...ICON_SOURCE.matchAll(/^\s*\|\s*'([a-z-]+)'$/gm)].map((match) => match[1]),
  )

  it('el catálogo de iconos se pudo leer', () => {
    expect(declared.size).toBeGreaterThan(20)
  })

  it('todos los iconos de módulos y grupos existen en LogisticsIcon', () => {
    for (const module of ALL_NAVIGATION_MODULES) {
      expect(declared.has(module.iconName), `${module.id} usa ${module.iconName}`).toBe(true)
    }
    for (const group of Object.values(NAVIGATION_GROUPS)) {
      expect(declared.has(group.iconName), `${group.id} usa ${group.iconName}`).toBe(true)
    }
  })
})

// ── orderedItems ─────────────────────────────────────────────────────────────

describe('orderedItems', () => {
  it('cubre exactamente los módulos existentes, sin faltantes ni sobrantes', () => {
    const ids = ALL_NAVIGATION_MODULES.map((module) => module.id).toSorted()
    expect(DEFAULT_PREFERENCES.orderedItems.toSorted()).toEqual(ids)
  })

  it('no tiene ids duplicados', () => {
    const { orderedItems } = DEFAULT_PREFERENCES
    expect(new Set(orderedItems).size).toBe(orderedItems.length)
  })

  it('lista los grupos en el orden canónico declarado', () => {
    const moduleById = new Map(ALL_NAVIGATION_MODULES.map((module) => [module.id, module]))
    const vistos: number[] = []

    for (const id of DEFAULT_PREFERENCES.orderedItems) {
      const groupId = moduleById.get(id)?.navigationGroup
      if (!groupId) continue
      const { order } = NAVIGATION_GROUPS[groupId]
      if (vistos.at(-1) !== order) vistos.push(order)
    }

    expect(vistos).toEqual([...vistos].toSorted((a, b) => a - b))
    expect(new Set(vistos).size).toBe(vistos.length)
  })

  it('los favoritos por defecto existen', () => {
    for (const id of DEFAULT_PREFERENCES.favoriteItems) {
      expect(ALL_NAVIGATION_MODULES.some((module) => module.id === id)).toBe(true)
    }
  })
})

// ── Permisos ─────────────────────────────────────────────────────────────────

describe('permisos de navegación', () => {
  it('el mapa de permisos se pudo leer', () => {
    expect(ALL_PERMISSION_STRINGS.size).toBeGreaterThan(100)
  })

  it('todo permiso del navbar existe en el mapa oficial', () => {
    for (const module of ALL_NAVIGATION_MODULES) {
      for (const permission of navPermissions(module)) {
        if (!permission.startsWith('logistics.')) continue // permisos legacy no logísticos
        expect(
          ALL_PERMISSION_STRINGS.has(permission),
          `${module.id} usa el permiso inexistente ${permission}`,
        ).toBe(true)
      }
    }
  })

  it('el permiso del navbar coincide con el guard de la ruta', () => {
    for (const module of ALL_NAVIGATION_MODULES) {
      const nav = navPermissions(module).filter((p) => p.startsWith('logistics.'))
      const guards = resolveGuardStrings(module.route).filter((p) => p.startsWith('logistics.'))
      if (nav.length === 0 || guards.length === 0) continue
      if (STRICTER_THAN_ROUTE[module.id]) continue

      expect(
        nav.some((permission) => guards.includes(permission)),
        `${module.id}: navbar=${nav.join('+')} ruta=${guards.join('+')}`,
      ).toBe(true)
    }
  })

  it('ningún guard del router referencia una clave inexistente del mapa', () => {
    for (const module of ALL_NAVIGATION_MODULES) {
      for (const guard of resolveGuardStrings(module.route)) {
        expect(guard.startsWith('DESCONOCIDO:'), guard).toBe(false)
      }
    }
  })
})

// ── Rutas ────────────────────────────────────────────────────────────────────

describe('rutas del navbar', () => {
  it('toda ruta del navbar está declarada en el router', () => {
    for (const module of ALL_NAVIGATION_MODULES) {
      expect(
        ROUTE_BY_PATH.has(module.route),
        `${module.id} apunta a ${module.route}, que no existe en AppRouter`,
      ).toBe(true)
    }
  })

  it('la ruta canónica de almacenes es /logistics/warehouses y la antigua redirige', () => {
    expect(ROUTER_SOURCE).toContain(
      '<Route\n              path="/warehouses"\n              element={<Navigate to="/logistics/warehouses" replace />}',
    )
    expect(
      ALL_NAVIGATION_MODULES.find((module) => module.id === 'warehouses')?.route,
    ).toBe('/logistics/warehouses')
    expect(ROUTE_BY_PATH.has('/logistics/warehouses')).toBe(true)
  })

  it('/logistics/evidence sigue redirigiendo a archivos y no tiene botón propio', () => {
    expect(ROUTER_SOURCE).toContain(
      '<Route path="/logistics/evidence" element={<Navigate to="/logistics/files" replace />} />',
    )
    expect(
      ALL_NAVIGATION_MODULES.some((module) => module.route === '/logistics/evidence'),
    ).toBe(false)
  })

  it('las rutas listas se integran en su grupo', () => {
    const board = ALL_NAVIGATION_MODULES.find((module) => module.id === 'inbound_docks_board')
    expect(board?.route).toBe('/logistics/inbound/docks')
    expect(board?.navigationGroup).toBe('inbound')
    expect(ROUTE_BY_PATH.has('/logistics/inbound/docks')).toBe(true)
  })

  it('las rutas no terminadas o internas se mantienen fuera del navbar', () => {
    // evaluations: el cliente devuelve listados vacíos fabricados (sin backend real).
    // quality/inspections: exige un case_id manual y ya vive en QualityQuarantinePhaseNav.
    const excluidas = [
      '/logistics/purchasing/evaluations',
      '/logistics/quality/inspections',
    ]
    for (const route of excluidas) {
      expect(ROUTE_BY_PATH.has(route), `${route} debe seguir existiendo`).toBe(true)
      expect(
        ALL_NAVIGATION_MODULES.some((module) => module.route === route),
        `${route} no está lista para el navbar`,
      ).toBe(false)
    }
  })
})

// ── Ruta activa ──────────────────────────────────────────────────────────────

describe('resolveActiveModuleId', () => {
  it('elige la ruta más específica cuando hay solapamiento', () => {
    expect(resolveActiveModuleId('/logistics/putaway/mobile', ALL_NAVIGATION_MODULES)).toBe('putaway_mobile')
    expect(resolveActiveModuleId('/logistics/putaway/orders', ALL_NAVIGATION_MODULES)).toBe('putaway')
    expect(resolveActiveModuleId('/logistics/putaway', ALL_NAVIGATION_MODULES)).toBe('putaway')
  })

  it('distingue requerimientos de su bandeja de revisión', () => {
    expect(
      resolveActiveModuleId('/logistics/purchasing/requisitions/review', ALL_NAVIGATION_MODULES),
    ).toBe('requisition_review_inbox')
    expect(
      resolveActiveModuleId('/logistics/purchasing/requisitions/nueva-id', ALL_NAVIGATION_MODULES),
    ).toBe('purchase_requisitions')
  })

  it('distingue el padre de investigación de sus hijos', () => {
    expect(resolveActiveModuleId('/research', ALL_NAVIGATION_MODULES)).toBe('research')
    expect(resolveActiveModuleId('/research/participants', ALL_NAVIGATION_MODULES)).toBe('participants')
    expect(resolveActiveModuleId('/research/sessions/42', ALL_NAVIGATION_MODULES)).toBe('sessions_study')
  })

  it('distingue el tablero de muelles de la cola y de la configuración', () => {
    expect(resolveActiveModuleId('/logistics/inbound/docks', ALL_NAVIGATION_MODULES)).toBe('inbound_docks_board')
    expect(resolveActiveModuleId('/logistics/inbound/docks/queue', ALL_NAVIGATION_MODULES)).toBe('inbound_docks_queue')
    expect(resolveActiveModuleId('/logistics/inbound/docks/settings', ALL_NAVIGATION_MODULES)).toBe('inbound_docks_settings')
    expect(resolveActiveModuleId('/logistics/inbound/docks/calendar', ALL_NAVIGATION_MODULES)).toBe('inbound_docks_board')
  })

  it('distingue el libro de inventario de los saldos', () => {
    expect(resolveActiveModuleId('/logistics/inventory/ledger/kardex', ALL_NAVIGATION_MODULES)).toBe('inventory_ledger')
    expect(resolveActiveModuleId('/logistics/inventory/stock/positions', ALL_NAVIGATION_MODULES)).toBe('inventory_balances')
  })

  it('reconoce las subrutas de detalle', () => {
    expect(resolveActiveModuleId('/logistics/vehicles/42/documents', ALL_NAVIGATION_MODULES)).toBe('vehicles')
  })

  it('devuelve un único módulo activo para toda ruta del router', () => {
    for (const row of ROUTE_ROWS) {
      if (row.path.includes(':') || row.path === '*') continue
      const activo = resolveActiveModuleId(row.path, ALL_NAVIGATION_MODULES)
      const coincidencias = ALL_NAVIGATION_MODULES.filter(
        (module) => module.id === activo,
      )
      expect(coincidencias.length).toBeLessThanOrEqual(1)
    }
  })

  it('devuelve null cuando la ruta no pertenece a ningún módulo', () => {
    expect(resolveActiveModuleId('/unauthorized', ALL_NAVIGATION_MODULES)).toBeNull()
  })

  it('no confunde rutas con prefijo común pero distinto segmento', () => {
    expect(
      resolveActiveModuleId('/logistics/file-deletion-requests', ALL_NAVIGATION_MODULES),
    ).toBe('file_deletion_requests')
  })
})

// ── Ctrl+K ───────────────────────────────────────────────────────────────────

describe('búsqueda de la paleta de comandos', () => {
  function buscar(query: string): string[] {
    return ALL_NAVIGATION_MODULES.filter((module) => matchesNavigationQuery(module, query)).map(
      (module) => module.id,
    )
  }

  it('encuentra hijos de grupos por jerga operativa', () => {
    expect(buscar('kardex')).toContain('inventory_ledger')
    expect(buscar('putaway')).toEqual(expect.arrayContaining(['putaway', 'putaway_mobile']))
    expect(buscar('muelle')).toEqual(
      expect.arrayContaining(['inbound_docks_queue', 'inbound_docks_board', 'inbound_docks_settings']),
    )
    expect(buscar('brevete')).toContain('driver_license_categories')
  })

  it('encuentra por etiqueta, descripción y nombre del grupo', () => {
    expect(buscar('Cuarentena')).toContain('quality_quarantine')
    expect(buscar('escaneo')).toContain('putaway_mobile')
    expect(buscar('compras')).toEqual(expect.arrayContaining(['purchase_orders', 'purchase_requisitions']))
  })

  it('ignora tildes y mayúsculas', () => {
    expect(buscar('ORGANIZACION')).toContain('organizations')
    expect(buscar('ubicacion dirigida')).toContain('putaway')
  })

  it('sigue alcanzando todos los módulos agrupados', () => {
    const agrupados = ALL_NAVIGATION_MODULES.filter((module) => module.navigationGroup)
    for (const module of agrupados) {
      expect(buscar(module.label), `${module.id} no aparece al buscar su propia etiqueta`).toContain(
        module.id,
      )
    }
  })

  it('con la búsqueda vacía devuelve la lista plana completa', () => {
    expect(buscar('')).toHaveLength(ALL_NAVIGATION_MODULES.length)
  })
})
