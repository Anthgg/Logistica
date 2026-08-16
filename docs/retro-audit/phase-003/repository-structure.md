# Estructura del Repositorio · Fase 003

## 1. Estructura Resumida del Repositorio Backend (`backend/`)

```text
backend/
├── alembic/                          # Migraciones de base de datos PostgreSQL
│   └── versions/                     # 33 versiones de migración estructuradas
├── app/
│   ├── api/                          # Enrutamiento raíz FastAPI
│   │   ├── routes/                   # Rutas compartidas (auth, health, reports, dashboard, etc.)
│   │   └── router.py                 # Montaje de api_router y create_logistics_router()
│   ├── core/                         # Configuración, settings, logging, seguridad básica
│   ├── database/                     # Conexión SQLAlchemy, sesiones y Base
│   ├── dependencies/                 # Inyección de dependencias (auth, db, csrf)
│   ├── models/                       # Modelos ORM compartidos (User, Warehouse, Shipment, etc.)
│   ├── modules/
│   │   └── logistics/                # DOMINIO LOGÍSTICO MODULAR (F003)
│   │       ├── access_resolver.py    # Resolución de acceso y RBAC contextual
│   │       ├── auth_dependencies.py  # Inyectores de LogisticsPrincipal y sesiones
│   │       ├── constants.py          # Constantes del dominio logístico
│   │       ├── dependencies.py       # Dependencias generales del módulo
│   │       ├── exceptions.py         # Excepciones estructuradas del dominio
│   │       ├── me_router.py          # Endpoint /api/logistics/me
│   │       ├── me_schemas.py         # Esquemas de perfil y permisos del usuario
│   │       ├── principal.py          # Entidad LogisticsPrincipal
│   │       ├── router.py             # Enrutador raíz _create_logistics_router()
│   │       │
│   │       ├── audit/                # [Transversal] Registro y sanitización de eventos de auditoría
│   │       ├── company_profile/      # Datos de la empresa, sedes y configuración legal
│   │       ├── cost_centers/         # Centros de costos para compras y requisiciones
│   │       ├── documents/            # [Transversal] Catálogo, series, plantillas, foliado y rendering
│   │       ├── drivers/              # Conductores, licencias, fotos y restricciones
│   │       ├── files/                # [Transversal] Almacenamiento seguro, hashes y evidencias
│   │       ├── gate_control/         # Control de accesos vehiculares a planta
│   │       ├── inbound/              # Recepción, muelles, inspección, diferencias y cuarentena
│   │       ├── integrations/         # [Transversal] Clientes de integración externa
│   │       ├── inventory/            # Ledger contable, balances y motor de putaway
│   │       ├── organization/         # Jerarquía organizacional y sucursales
│   │       ├── partners/             # Socios de negocio, proveedores y transportistas
│   │       ├── procurement/          # Requisiciones, cotizaciones, evaluaciones y aprobaciones
│   │       ├── products/             # Catálogo de productos, categorías y marcas
│   │       ├── purchase_orders/      # Órdenes de compra directas
│   │       ├── rbac/                 # Roles, permisos y asignaciones
│   │       ├── routes_module/        # [Transversal] Servicios de cálculo y gestión de rutas
│   │       ├── ruc/                  # Integración con padrón RUC y validación SUNAT
│   │       ├── security/             # Autenticación continua y políticas Step-Up
│   │       ├── shared/               # Primitivas y DTOs comunes entre submódulos
│   │       ├── units/                # Unidades de medida y motor de conversiones
│   │       ├── vehicle_verifications/# Verificación y auditoría de flota vehicular
│   │       ├── vehicles/             # Vehículos, capacidades, placas y marcas
│   │       └── warehouses/           # Almacenes, zonas, ubicaciones, etiquetas y códigos QR
│   ├── repositories/                 # Repositorios base
│   ├── schemas/                      # Esquemas generales Pydantic
│   └── services/                     # Servicios base y transversales
└── tests/                            # Suite completa de pruebas automatizadas
    ├── unit/
    ├── integration/
    └── security/
```

---

## 2. Estructura Resumida del Repositorio Frontend (`frontend/`)

```text
frontend/
├── src/
│   ├── api/                          # Clientes HTTP y adaptadores de API
│   │   ├── api-client.ts             # Cliente HTTP canónico con CSRF, Step-Up y refresh
│   │   ├── auth-api.ts               # Autenticación y sesiones
│   │   ├── documents-api.ts          # Integración con motor documental
│   │   ├── files-api.ts              # Integración con repositorio de archivos
│   │   ├── logistics-api.ts          # Integración con /api/logistics/me y seguridad
│   │   └── ...                       # Clientes tipados por dominio
│   ├── components/                   # Componentes UI reutilizables
│   │   ├── ui/                       # Primitivas de diseño accesibles
│   │   └── [domain]/                 # Paneles, wizards y modales de dominio
│   ├── contexts/                     # Proveedores de estado global
│   │   ├── AuthContext.tsx           # Contexto de autenticación y usuario
│   │   ├── ContinuousAuthProvider.tsx# Contexto de verificación continua y Step-Up
│   │   └── I18nProvider.tsx          # Contexto de internacionalización
│   ├── features/                     # Módulos encapsulados por funcionalidad
│   │   ├── continuous-auth/          # Manejo de desafíos de seguridad Step-Up
│   │   ├── gate-control/             # Interfaz de garita y control de ingreso
│   │   ├── inbound-docks/            # Gestión visual de muelles y descarga
│   │   ├── inbound-receiving/        # Pantalla de recepción y escaneo de bultos
│   │   ├── inventory-balances/       # Consulta y exportación de saldos
│   │   ├── inventory-ledger/         # Kárdex y movimientos de stock
│   │   ├── logistics-me/             # Perfil logístico y roles del operador
│   │   ├── logistics-permissions/    # Matriz y asignación de permisos
│   │   ├── procurement-approvals/    # Bandeja de aprobación de compras
│   │   ├── purchase-orders/          # Gestión de órdenes de compra
│   │   ├── putaway/                  # Sugerencias y confirmación de ubicación
│   │   ├── quality-inspection-plans/ # Planes de inspección de calidad
│   │   ├── quarantine/               # Gestión de mercancía en cuarentena
│   │   ├── reception-differences/    # Registro y resolución de mermas/sobrantes
│   │   ├── shipments/                # Despachos y seguimiento de envíos
│   │   └── supplier-evaluation/      # Evaluación técnica y de riesgo de proveedores
│   ├── hooks/                        # Custom hooks compartidos
│   ├── pages/                        # Páginas enrutadas por React Router
│   ├── router/                       # Definición de rutas (`AppRouter.tsx`)
│   ├── styles/                       # CSS modular y variables de diseño
│   ├── types/                        # Tipos TypeScript y DTOs
│   └── utils/                        # Utilidades de fecha, validación y permisos
└── tests/                            # Pruebas unitarias e integración de interfaz
```
