import type { LogisticsIconName } from '../common/LogisticsIcon'

export interface NavigationModule {
  id: string
  label: string
  route: string
  iconName: LogisticsIconName
  description?: string
  /** Sinónimos y jerga operativa para que Ctrl+K encuentre el módulo. */
  keywords?: readonly string[]
  badge?: number
  permission?: string
  anyOfPermissions?: readonly string[]
  legacyAlwaysAllowed?: boolean
  category?: 'operaciones' | 'analitica' | 'investigacion' | 'seguridad' | 'sistema' | 'maestros'
  navigationGroup?: NavigationGroupId
}

export type NavigationGroupId =
  | 'inbound'
  | 'quality'
  | 'inventory'
  | 'purchasing'
  | 'catalogs'
  | 'fleet'
  | 'drivers'
  | 'organization'
  | 'documents'
  | 'access'
  | 'research'
  | 'account'

export interface NavigationGroup {
  id: NavigationGroupId
  label: string
  description: string
  iconName: LogisticsIconName
  /**
   * Orden canónico del grupo dentro de la barra. La posición real la sigue
   * decidiendo `orderedItems` (para respetar el reordenamiento del usuario),
   * pero `DEFAULT_PREFERENCES` debe listar los grupos siguiendo este orden.
   */
  order: number
  /** Etiqueta accesible del botón que abre el desplegable. */
  ariaLabel: string
}

export type NavigationDisplayItem =
  | { type: 'module'; module: NavigationModule }
  | { type: 'group'; group: NavigationGroup; modules: NavigationModule[] }

export const NAVIGATION_GROUPS: Record<NavigationGroupId, NavigationGroup> = {
  inbound: {
    id: 'inbound',
    label: 'Recepción',
    description: 'Garita, muelles y diferencias de recepción',
    iconName: 'dock',
    order: 1,
    ariaLabel: 'Abrir Recepción: garita, muelles y diferencias',
  },
  quality: {
    id: 'quality',
    label: 'Calidad',
    description: 'Planes, inspecciones y cuarentena',
    iconName: 'shield',
    order: 2,
    ariaLabel: 'Abrir Calidad: planes, inspecciones y cuarentena',
  },
  inventory: {
    id: 'inventory',
    label: 'Inventario',
    description: 'Existencias, kardex y ubicación dirigida',
    iconName: 'box',
    order: 3,
    ariaLabel: 'Abrir Inventario: existencias, kardex y ubicación',
  },
  purchasing: {
    id: 'purchasing',
    label: 'Compras',
    description: 'Requerimientos, órdenes y aprobaciones',
    iconName: 'document',
    order: 4,
    ariaLabel: 'Abrir Compras: requerimientos, órdenes y aprobaciones',
  },
  catalogs: {
    id: 'catalogs',
    label: 'Catálogos',
    description: 'Productos, unidades, socios y centros de costo',
    iconName: 'grid',
    order: 5,
    ariaLabel: 'Abrir Catálogos: productos, unidades, socios y centros de costo',
  },
  fleet: {
    id: 'fleet',
    label: 'Flota',
    description: 'Vehículos, marcas, modelos y verificaciones',
    iconName: 'truck',
    order: 6,
    ariaLabel: 'Abrir Flota: vehículos, marcas, modelos y verificaciones',
  },
  drivers: {
    id: 'drivers',
    label: 'Conductores',
    description: 'Padrón de conductores, licencias y alertas',
    iconName: 'user',
    order: 7,
    ariaLabel: 'Abrir Conductores: padrón, licencias y alertas',
  },
  organization: {
    id: 'organization',
    label: 'Organización',
    description: 'Empresa, sedes y almacenes',
    iconName: 'building',
    order: 8,
    ariaLabel: 'Abrir Organización: empresa, sedes y almacenes',
  },
  documents: {
    id: 'documents',
    label: 'Documentos y archivos',
    description: 'Documentos logísticos y repositorio de archivos',
    iconName: 'archive',
    order: 9,
    ariaLabel: 'Abrir Documentos y archivos',
  },
  access: {
    id: 'access',
    label: 'Accesos y auditoría',
    description: 'Roles, asignaciones, permisos y trazabilidad',
    iconName: 'lock',
    order: 10,
    ariaLabel: 'Abrir Accesos y auditoría',
  },
  research: {
    id: 'research',
    label: 'Investigación',
    description: 'Biometría, participantes y sesiones de estudio',
    iconName: 'research',
    order: 11,
    ariaLabel: 'Abrir Investigación: biometría, participantes y sesiones',
  },
  account: {
    id: 'account',
    label: 'Mi cuenta',
    description: 'Perfil, dispositivos y seguridad de la sesión',
    iconName: 'key',
    order: 12,
    ariaLabel: 'Abrir Mi cuenta: perfil, dispositivos y seguridad',
  },
}

export interface NavigationPreferences {
  orderedItems: string[]
  hiddenItems: string[]
  favoriteItems: string[]
  showLabels: boolean
  density: 'compact' | 'comfortable'
  alignment: 'left' | 'center' | 'right'
  autoHideEnabled: boolean
  autoHideDelay: number // en segundos (30, 60, 120, -1 para nunca)
}

export const DEFAULT_PREFERENCES: NavigationPreferences = {
  orderedItems: [
    'dashboard',
    'shipments',
    'routes',
    'incidents',
    'clients',
    'reports',
    // Recepción
    'gate_control_dashboard',
    'inbound_docks_queue',
    'inbound_docks_board',
    'inbound_docks_settings',
    'reception_differences',
    // Calidad
    'quality_inspection_plans',
    'quality_quarantine',
    // Inventario
    'inventory',
    'inventory_ledger',
    'inventory_balances',
    'putaway',
    'putaway_mobile',
    // Compras
    'purchase_requisitions',
    'requisition_review_inbox',
    'purchase_orders',
    'procurement_approval_inbox',
    'procurement_approval_policies',
    // Catálogos
    'catalog_products',
    'catalog_units',
    'catalog_business_partners',
    'cost_centers',
    // Flota
    'vehicles',
    'vehicle_makes',
    'vehicle_models',
    'vehicle_verifications',
    // Conductores
    'drivers',
    'driver_license_categories',
    'driver_alerts',
    // Organización
    'organizations',
    'branches',
    'warehouses',
    'company_settings',
    // Documentos y archivos
    'documents',
    'files',
    'file_deletion_requests',
    // Accesos y auditoría
    'roles',
    'role_assignments',
    'permissions_catalog',
    'audit_events',
    // Integraciones
    'ruc_integration',
    // Investigación
    'research',
    'participants',
    'sessions_study',
    // Mi cuenta
    'profile',
    'sessions_devices',
    'change_password',
    'security_status',
    'evaluations',
    'models_status',
  ],
  hiddenItems: [],
  favoriteItems: ['dashboard', 'shipments', 'routes', 'inventory'],
  showLabels: false,
  density: 'comfortable',
  alignment: 'center',
  autoHideEnabled: true,
  autoHideDelay: 60,
}

export const ALL_NAVIGATION_MODULES: NavigationModule[] = [
  {
    id: 'dashboard',
    label: 'Panel principal',
    route: '/dashboard',
    iconName: 'dashboard',
    description: 'Resumen operativo del día',
    keywords: ['inicio', 'home', 'panel', 'resumen'],
    legacyAlwaysAllowed: true,
    category: 'operaciones',
  },
  {
    id: 'shipments',
    label: 'Operaciones / Envíos',
    route: '/shipments',
    iconName: 'package',
    description: 'Seguimiento de envíos en curso',
    keywords: ['envio', 'envios', 'despacho', 'entrega', 'tracking'],
    legacyAlwaysAllowed: true,
    category: 'operaciones',
  },
  {
    id: 'routes',
    label: 'Rutas',
    route: '/routes',
    iconName: 'route',
    description: 'Planificación de recorridos',
    keywords: ['ruta', 'rutas', 'recorrido', 'reparto'],
    legacyAlwaysAllowed: true,
    category: 'operaciones',
  },
  {
    id: 'incidents',
    label: 'Incidencias',
    route: '/incidents',
    iconName: 'alert',
    description: 'Eventos y novedades operativas',
    keywords: ['incidencia', 'novedad', 'problema', 'evento'],
    legacyAlwaysAllowed: true,
    category: 'operaciones',
  },
  {
    id: 'clients',
    label: 'Clientes',
    route: '/clients',
    iconName: 'clients',
    description: 'Cartera de clientes',
    keywords: ['cliente', 'clientes', 'cartera'],
    legacyAlwaysAllowed: true,
    category: 'operaciones',
  },
  {
    id: 'reports',
    label: 'Indicadores / Reportes',
    route: '/reports',
    iconName: 'reports',
    description: 'Indicadores y reportes de gestión',
    keywords: ['reporte', 'indicador', 'kpi', 'metrica', 'analitica'],
    permission: 'viewReports',
    legacyAlwaysAllowed: true,
    category: 'analitica',
  },

  // ─── Recepción ────────────────────────────────────────────────────────────
  {
    id: 'gate_control_dashboard',
    label: 'Garita de Ingreso',
    route: '/logistics/inbound/gate-control',
    iconName: 'shield',
    description: 'Registro y verificación de ingreso vehicular',
    keywords: ['garita', 'gate', 'ingreso', 'porteria', 'checkin', 'cpv'],
    permission: 'logistics.gate_check_ins.read',
    category: 'operaciones',
    navigationGroup: 'inbound',
  },
  {
    id: 'inbound_docks_queue',
    label: 'Cola de Muelles',
    route: '/logistics/inbound/docks/queue',
    iconName: 'list',
    description: 'Vehículos autorizados pendientes de asignación',
    keywords: ['muelle', 'muelles', 'dock', 'cola', 'turno', 'espera'],
    permission: 'logistics.inbound_dock_queue.read',
    category: 'operaciones',
    navigationGroup: 'inbound',
  },
  {
    id: 'inbound_docks_board',
    label: 'Tablero de Muelles',
    route: '/logistics/inbound/docks',
    iconName: 'grid',
    description: 'Estado en vivo de asignaciones y descarga',
    keywords: ['muelle', 'muelles', 'dock', 'tablero', 'board', 'descarga', 'operaciones'],
    permission: 'logistics.inbound_dock_queue.read',
    category: 'operaciones',
    navigationGroup: 'inbound',
  },
  {
    id: 'inbound_docks_settings',
    label: 'Configuración Muelles',
    route: '/logistics/inbound/docks/settings',
    iconName: 'sliders',
    description: 'Administración de puertas y muelles',
    keywords: ['muelle', 'muelles', 'dock', 'puerta', 'configuración'],
    permission: 'logistics.warehouse_docks.manage',
    category: 'sistema',
    navigationGroup: 'inbound',
  },
  {
    id: 'reception_differences',
    label: 'Diferencias Recepción',
    route: '/logistics/inbound/reception-differences',
    iconName: 'alert',
    description: 'Faltantes, sobrantes y averías de recepción',
    keywords: ['diferencia', 'faltante', 'sobrante', 'averia', 'dif'],
    permission: 'logistics.reception_difference_cases.read',
    category: 'operaciones',
    navigationGroup: 'inbound',
  },

  // ─── Calidad ──────────────────────────────────────────────────────────────
  {
    id: 'quality_inspection_plans',
    label: 'Planes de Calidad',
    route: '/logistics/quality/plans',
    iconName: 'clipboard',
    description: 'Planes, tolerancias y muestreos de calidad',
    keywords: ['calidad', 'plan', 'tolerancia', 'muestreo', 'inspeccion'],
    permission: 'logistics.quality_plan.read',
    category: 'maestros',
    navigationGroup: 'quality',
  },
  {
    id: 'quality_quarantine',
    label: 'Cuarentena',
    route: '/logistics/quality/quarantine',
    iconName: 'shield',
    description: 'Casos retenidos, inspecciones y liberación',
    keywords: ['cuarentena', 'retenido', 'liberacion', 'rechazo', 'no conformidad', 'inspeccion'],
    permission: 'logistics.quality_quarantine.read',
    category: 'operaciones',
    navigationGroup: 'quality',
  },

  // ─── Inventario ───────────────────────────────────────────────────────────
  {
    id: 'inventory',
    label: 'Inventario',
    route: '/inventory',
    iconName: 'box',
    description: 'Existencias operativas por almacén',
    keywords: ['inventario', 'stock', 'existencia', 'saldo'],
    legacyAlwaysAllowed: true,
    category: 'operaciones',
    navigationGroup: 'inventory',
  },
  {
    id: 'inventory_ledger',
    label: 'Libro de Inventario',
    route: '/logistics/inventory/ledger',
    iconName: 'clipboard',
    description: 'Movimientos y kardex técnico',
    keywords: ['kardex', 'ledger', 'libro', 'movimiento', 'conciliacion', 'asiento'],
    permission: 'logistics.inventory_ledger.read',
    category: 'operaciones',
    navigationGroup: 'inventory',
  },
  {
    id: 'inventory_balances',
    label: 'Saldos de Inventario',
    route: '/logistics/inventory/stock',
    iconName: 'box',
    description: 'Consulta técnica de saldos por posición',
    keywords: ['saldo', 'balance', 'stock', 'existencia', 'posicion', 'ubicacion'],
    permission: 'logistics.inventory_ledger.read',
    category: 'operaciones',
    navigationGroup: 'inventory',
  },
  {
    id: 'putaway',
    label: 'Ubicación Dirigida',
    route: '/logistics/putaway',
    iconName: 'route',
    description: 'Planificación y ejecución de putaway',
    keywords: ['putaway', 'ubicacion', 'acomodo', 'almacenamiento', 'tarea'],
    permission: 'logistics.putaway.read',
    category: 'operaciones',
    navigationGroup: 'inventory',
  },
  {
    id: 'putaway_mobile',
    label: 'Ubicación Móvil',
    route: '/logistics/putaway/mobile',
    iconName: 'sessions',
    description: 'Ejecución de tareas de ubicación mediante escaneo',
    keywords: ['putaway', 'movil', 'mobile', 'escaneo', 'scanner', 'terminal'],
    permission: 'logistics.putaway.execute',
    category: 'operaciones',
    navigationGroup: 'inventory',
  },

  // ─── Compras ──────────────────────────────────────────────────────────────
  {
    id: 'purchase_requisitions',
    label: 'Requerimientos de Compra (REQ)',
    route: '/logistics/purchasing/requisitions',
    iconName: 'document',
    description: 'Solicitudes internas de abastecimiento',
    keywords: ['req', 'requerimiento', 'solicitud', 'abastecimiento', 'compra'],
    permission: 'logistics.purchase_requisitions.read',
    category: 'operaciones',
    navigationGroup: 'purchasing',
  },
  {
    id: 'requisition_review_inbox',
    label: 'Bandeja de Revisión REQ',
    route: '/logistics/purchasing/requisitions/review',
    iconName: 'check-square',
    description: 'Revisión y devolución de requerimientos',
    keywords: ['req', 'revision', 'bandeja', 'aprobar', 'devolver'],
    permission: 'logistics.purchase_requisitions.review',
    category: 'operaciones',
    navigationGroup: 'purchasing',
  },
  {
    id: 'purchase_orders',
    label: 'Órdenes de Compra',
    route: '/logistics/purchasing/purchase-orders',
    iconName: 'package',
    description: 'Emisión y seguimiento de órdenes de compra',
    keywords: ['oc', 'orden', 'compra', 'proveedor', 'purchase order'],
    permission: 'logistics.purchase_orders.read',
    category: 'operaciones',
    navigationGroup: 'purchasing',
  },
  {
    id: 'procurement_approval_inbox',
    label: 'Aprobaciones de Compra',
    route: '/logistics/purchasing/approvals/inbox',
    iconName: 'check-square',
    description: 'Decisiones de aprobación pendientes',
    keywords: ['aprobacion', 'aprobar', 'bandeja', 'visto bueno', 'firma'],
    anyOfPermissions: [
      'logistics.procurement_approvals.read',
      'logistics.purchase_orders.approve',
    ],
    category: 'operaciones',
    navigationGroup: 'purchasing',
  },
  {
    id: 'procurement_approval_policies',
    label: 'Políticas de Aprobación',
    route: '/logistics/purchasing/approval-policies',
    iconName: 'sliders',
    description: 'Umbrales y cadenas de aprobación',
    keywords: ['politica', 'umbral', 'cadena', 'aprobacion', 'regla'],
    anyOfPermissions: [
      'logistics.procurement_approval_policies.read',
      'logistics.procurement_approval_policies.create',
      'logistics.procurement_approval_policies.update',
      'logistics.procurement_approval_policies.activate',
    ],
    category: 'sistema',
    navigationGroup: 'purchasing',
  },

  // ─── Catálogos ────────────────────────────────────────────────────────────
  {
    id: 'catalog_products',
    label: 'Catálogo Productos',
    route: '/logistics/products',
    iconName: 'box',
    description: 'Maestro de productos y presentaciones',
    keywords: ['producto', 'sku', 'articulo', 'catalogo', 'material'],
    permission: 'logistics.products.read',
    category: 'maestros',
    navigationGroup: 'catalogs',
  },
  {
    id: 'catalog_units',
    label: 'Unidades y Conversiones',
    route: '/logistics/units',
    iconName: 'sliders',
    description: 'Unidades de medida y factores de conversión',
    keywords: ['unidad', 'medida', 'conversion', 'factor', 'um'],
    permission: 'logistics.units.read',
    category: 'maestros',
    navigationGroup: 'catalogs',
  },
  {
    id: 'catalog_business_partners',
    label: 'Socios de Negocio',
    route: '/logistics/business-partners',
    iconName: 'users',
    description: 'Proveedores, clientes y transportistas',
    keywords: ['socio', 'proveedor', 'cliente', 'transportista', 'partner', 'ruc'],
    permission: 'logistics.business_partners.read',
    category: 'maestros',
    navigationGroup: 'catalogs',
  },
  {
    id: 'cost_centers',
    label: 'Centros de Costo',
    route: '/logistics/catalog/cost-centers',
    iconName: 'grid',
    description: 'Imputación contable de los consumos',
    keywords: ['centro', 'costo', 'cc', 'contable', 'imputacion'],
    permission: 'logistics.cost_centers.read',
    category: 'maestros',
    navigationGroup: 'catalogs',
  },

  // ─── Flota ────────────────────────────────────────────────────────────────
  {
    id: 'vehicles',
    label: 'Vehículos & Flota',
    route: '/logistics/vehicles',
    iconName: 'truck',
    description: 'Padrón de unidades y su documentación',
    keywords: ['vehiculo', 'unidad', 'placa', 'flota', 'camion', 'tracto'],
    permission: 'logistics.vehicles.read',
    category: 'maestros',
    navigationGroup: 'fleet',
  },
  {
    id: 'vehicle_makes',
    label: 'Marcas Vehiculares',
    route: '/logistics/vehicle-makes',
    iconName: 'layers',
    description: 'Maestro de marcas homologadas',
    keywords: ['marca', 'vehiculo', 'fabricante', 'homologacion'],
    permission: 'logistics.vehicles.read',
    category: 'maestros',
    navigationGroup: 'fleet',
  },
  {
    id: 'vehicle_models',
    label: 'Modelos Vehiculares',
    route: '/logistics/vehicle-models',
    iconName: 'sliders',
    description: 'Modelos asociados a cada marca',
    keywords: ['modelo', 'vehiculo', 'marca', 'version'],
    permission: 'logistics.vehicles.read',
    category: 'maestros',
    navigationGroup: 'fleet',
  },
  {
    id: 'vehicle_verifications',
    label: 'Verificaciones Vehiculares',
    route: '/logistics/integrations/vehicle-verifications',
    iconName: 'shield',
    description: 'Contraste de unidades con fuentes externas',
    keywords: ['verificacion', 'sunarp', 'mtc', 'contraste', 'placa'],
    permission: 'logistics.vehicles.verify',
    category: 'operaciones',
    navigationGroup: 'fleet',
  },

  // ─── Conductores ──────────────────────────────────────────────────────────
  {
    id: 'drivers',
    label: 'Conductores',
    route: '/logistics/drivers',
    iconName: 'user',
    description: 'Padrón de conductores y sus licencias',
    keywords: ['conductor', 'chofer', 'licencia', 'brevete', 'piloto'],
    permission: 'logistics.drivers.read',
    category: 'maestros',
    navigationGroup: 'drivers',
  },
  {
    id: 'driver_license_categories',
    label: 'Categorías de Licencia',
    route: '/logistics/driver-license-categories',
    iconName: 'sliders',
    description: 'Categorías habilitantes por tipo de unidad',
    keywords: ['licencia', 'categoria', 'brevete', 'habilitacion'],
    permission: 'logistics.drivers.read',
    category: 'maestros',
    navigationGroup: 'drivers',
  },
  {
    id: 'driver_alerts',
    label: 'Alertas de Conductores',
    route: '/logistics/alerts/drivers',
    iconName: 'alert',
    description: 'Vencimientos y bloqueos de conductores',
    keywords: ['alerta', 'vencimiento', 'bloqueo', 'conductor'],
    permission: 'logistics.drivers.read',
    category: 'operaciones',
    navigationGroup: 'drivers',
  },

  // ─── Organización ─────────────────────────────────────────────────────────
  {
    id: 'organizations',
    label: 'Organizaciones',
    route: '/logistics/organizations',
    iconName: 'building',
    description: 'Estructura de empresas del grupo',
    keywords: ['organizacion', 'empresa', 'grupo', 'holding'],
    permission: 'logistics.organizations.read',
    category: 'sistema',
    navigationGroup: 'organization',
  },
  {
    id: 'branches',
    label: 'Sedes',
    route: '/logistics/branches',
    iconName: 'location',
    description: 'Sedes operativas por organización',
    keywords: ['sede', 'sucursal', 'branch', 'local'],
    permission: 'logistics.branches.read',
    category: 'sistema',
    navigationGroup: 'organization',
  },
  {
    id: 'warehouses',
    label: 'Almacenes',
    route: '/logistics/warehouses',
    iconName: 'dock',
    description: 'Almacenes y zonas de almacenamiento',
    keywords: ['almacen', 'deposito', 'warehouse', 'zona', 'bodega'],
    permission: 'logistics.warehouses.read',
    category: 'operaciones',
    navigationGroup: 'organization',
  },
  {
    id: 'company_settings',
    label: 'Ficha Empresa',
    route: '/logistics/company-profile',
    iconName: 'info',
    description: 'Datos fiscales y ficha de la empresa',
    keywords: ['empresa', 'ficha', 'fiscal', 'ruc', 'razon social'],
    permission: 'logistics.company_profile.read',
    category: 'sistema',
    navigationGroup: 'organization',
  },

  // ─── Documentos y archivos ────────────────────────────────────────────────
  {
    id: 'documents',
    label: 'Documentos',
    route: '/logistics/documents',
    iconName: 'document',
    description: 'Documentos logísticos emitidos',
    keywords: ['documento', 'guia', 'comprobante', 'emision'],
    anyOfPermissions: ['logistics.documents.read'],
    category: 'operaciones',
    navigationGroup: 'documents',
  },
  {
    id: 'files',
    label: 'Repositorio de Archivos',
    route: '/logistics/files',
    iconName: 'archive',
    description: 'Archivos, versiones y evidencias',
    keywords: ['archivo', 'file', 'repositorio', 'adjunto', 'evidencia', 'custodia'],
    permission: 'logistics.files.read',
    category: 'sistema',
    navigationGroup: 'documents',
  },
  {
    id: 'file_deletion_requests',
    label: 'Solicitudes de Eliminación',
    route: '/logistics/file-deletion-requests',
    iconName: 'x',
    description: 'Bajas de archivos pendientes de aprobación',
    keywords: ['eliminacion', 'baja', 'borrar', 'archivo', 'solicitud'],
    permission: 'logistics.files.read',
    category: 'sistema',
    navigationGroup: 'documents',
  },

  // ─── Accesos y auditoría ──────────────────────────────────────────────────
  {
    id: 'roles',
    label: 'Roles',
    route: '/logistics/roles',
    iconName: 'lock',
    description: 'Definición de roles del sistema',
    keywords: ['rol', 'roles', 'perfil', 'rbac'],
    permission: 'logistics.roles.read',
    category: 'seguridad',
    navigationGroup: 'access',
  },
  {
    id: 'role_assignments',
    label: 'Asignaciones',
    route: '/logistics/role-assignments',
    iconName: 'users',
    description: 'Roles asignados por usuario y ámbito',
    keywords: ['asignacion', 'usuario', 'rol', 'scope', 'ambito'],
    permission: 'logistics.role_assignments.read',
    category: 'seguridad',
    navigationGroup: 'access',
  },
  {
    id: 'permissions_catalog',
    label: 'Permisos',
    route: '/logistics/permissions',
    iconName: 'shield',
    description: 'Catálogo de permisos disponibles',
    keywords: ['permiso', 'capability', 'rbac', 'catalogo'],
    permission: 'logistics.permissions.read',
    category: 'seguridad',
    navigationGroup: 'access',
  },
  {
    id: 'audit_events',
    label: 'Auditoría',
    route: '/logistics/audit-events',
    iconName: 'activity',
    description: 'Trazabilidad de acciones sensibles',
    keywords: ['auditoria', 'audit', 'log', 'trazabilidad', 'historial'],
    permission: 'logistics.audit.read',
    category: 'seguridad',
    navigationGroup: 'access',
  },

  // ─── Integraciones ────────────────────────────────────────────────────────
  {
    id: 'ruc_integration',
    label: 'Consulta de RUC & Padrones',
    route: '/logistics/ruc',
    iconName: 'search',
    description: 'Consulta de RUC, padrones e importaciones',
    keywords: ['ruc', 'sunat', 'padron', 'contribuyente', 'consulta'],
    permission: 'logistics.ruc_lookup.read',
    category: 'operaciones',
  },

  // ─── Investigación ────────────────────────────────────────────────────────
  {
    id: 'research',
    label: 'Biometría',
    route: '/research',
    iconName: 'research',
    description: 'Panel del estudio biométrico',
    keywords: ['biometria', 'investigacion', 'estudio', 'research'],
    legacyAlwaysAllowed: true,
    category: 'investigacion',
    navigationGroup: 'research',
  },
  {
    id: 'participants',
    label: 'Participantes',
    route: '/research/participants',
    iconName: 'users',
    description: 'Registro de participantes del estudio',
    keywords: ['participante', 'sujeto', 'estudio', 'muestra'],
    legacyAlwaysAllowed: true,
    category: 'investigacion',
    navigationGroup: 'research',
  },
  {
    id: 'sessions_study',
    label: 'Sesiones de estudio',
    route: '/research/sessions',
    iconName: 'timeline',
    description: 'Sesiones experimentales registradas',
    keywords: ['sesion', 'estudio', 'experimento', 'captura'],
    legacyAlwaysAllowed: true,
    category: 'investigacion',
    navigationGroup: 'research',
  },

  // ─── Mi cuenta ────────────────────────────────────────────────────────────
  {
    id: 'profile',
    label: 'Mi perfil',
    route: '/profile',
    iconName: 'user',
    description: 'Datos de tu cuenta',
    keywords: ['perfil', 'cuenta', 'usuario', 'mis datos'],
    legacyAlwaysAllowed: true,
    category: 'sistema',
    navigationGroup: 'account',
  },
  {
    id: 'sessions_devices',
    label: 'Dispositivos',
    route: '/sessions',
    iconName: 'sessions',
    description: 'Sesiones activas y dispositivos',
    keywords: ['dispositivo', 'sesion', 'device', 'equipo'],
    legacyAlwaysAllowed: true,
    category: 'seguridad',
    navigationGroup: 'account',
  },
  {
    id: 'change_password',
    label: 'Cambiar contraseña',
    route: '/change-password',
    iconName: 'key',
    description: 'Actualiza tu clave de acceso',
    keywords: ['contrasena', 'password', 'clave', 'seguridad'],
    legacyAlwaysAllowed: true,
    category: 'seguridad',
    navigationGroup: 'account',
  },
  {
    id: 'security_status',
    label: 'Estado de seguridad',
    route: '/security/continuous-auth',
    iconName: 'shield',
    description: 'Nivel de autenticación continua',
    keywords: ['seguridad', 'riesgo', 'autenticacion', 'continua'],
    legacyAlwaysAllowed: true,
    category: 'seguridad',
    navigationGroup: 'account',
  },
  {
    id: 'evaluations',
    label: 'Evaluaciones continuas',
    route: '/admin/continuous-auth/evaluations',
    iconName: 'activity',
    description: 'Historial de evaluaciones del modelo',
    keywords: ['evaluacion', 'modelo', 'continua', 'riesgo'],
    legacyAlwaysAllowed: true,
    category: 'seguridad',
    navigationGroup: 'account',
  },
  {
    id: 'models_status',
    label: 'Estado de modelos',
    route: '/admin/models/status',
    iconName: 'layers',
    description: 'Disponibilidad de los modelos biométricos',
    keywords: ['modelo', 'estado', 'biometria', 'salud'],
    legacyAlwaysAllowed: true,
    category: 'seguridad',
    navigationGroup: 'account',
  },
]

/** Normaliza para buscar sin depender de tildes ni mayúsculas. */
function normalizeSearchText(value: string): string {
  return value
    .toLocaleLowerCase('es')
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
}

/**
 * Coincidencia usada por Ctrl+K. Busca sobre etiqueta, descripción, ruta,
 * sinónimos y el nombre del grupo, de modo que agrupar visualmente nunca
 * saca un módulo del buscador.
 */
export function matchesNavigationQuery(
  module: NavigationModule,
  query: string,
): boolean {
  const needle = normalizeSearchText(query).trim()
  if (!needle) return true

  const group = module.navigationGroup
    ? NAVIGATION_GROUPS[module.navigationGroup]
    : null

  const haystack = [
    module.label,
    module.description ?? '',
    module.route,
    group?.label ?? '',
    ...(module.keywords ?? []),
  ]
    .map(normalizeSearchText)
    .join(' ')

  return needle.split(/\s+/).every((term) => haystack.includes(term))
}

export function isRouteActive(pathname: string, route: string): boolean {
  return pathname === route || pathname.startsWith(`${route}/`)
}

/**
 * Devuelve el id del módulo que corresponde a la ruta actual. Cuando varias
 * rutas encajan (por ejemplo `/logistics/putaway` y `/logistics/putaway/mobile`)
 * gana la más específica, de modo que solo un botón queda marcado como activo.
 */
export function resolveActiveModuleId(
  pathname: string,
  modules: readonly NavigationModule[],
): string | null {
  let best: NavigationModule | null = null

  for (const module of modules) {
    if (!isRouteActive(pathname, module.route)) continue
    if (!best || module.route.length > best.route.length) {
      best = module
    }
  }

  return best?.id ?? null
}

export function groupNavigationModules(
  modules: NavigationModule[],
): NavigationDisplayItem[] {
  const groupedModules = new Map<NavigationGroupId, NavigationModule[]>()

  for (const module of modules) {
    if (!module.navigationGroup) continue
    const current = groupedModules.get(module.navigationGroup) ?? []
    current.push(module)
    groupedModules.set(module.navigationGroup, current)
  }

  const emittedGroups = new Set<NavigationGroupId>()

  return modules.flatMap((module): NavigationDisplayItem[] => {
    const groupId = module.navigationGroup
    if (!groupId) return [{ type: 'module', module }]
    if (emittedGroups.has(groupId)) return []

    const children = groupedModules.get(groupId) ?? []
    if (children.length < 2) {
      return [{ type: 'module', module }]
    }

    emittedGroups.add(groupId)
    return [
      {
        type: 'group',
        group: NAVIGATION_GROUPS[groupId],
        modules: children,
      },
    ]
  })
}
