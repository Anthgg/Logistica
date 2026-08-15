# Matriz de Dependencias y Ciclos · Fase 003

## 1. Matriz de Dependencias entre Submódulos Backend

La siguiente matriz documenta las llamadas e importaciones directas entre submódulos en `backend/app/modules/logistics/`:

| Submódulo Origen | Submódulos Destino Importados | Componentes Compartidos Utilizados | Tipo de Dependencia | Evaluación y Evidencia |
| :--- | :--- | :--- | :--- | :--- |
| **audit** | *Ninguno* | `models_event.py` | Standalone | VÁLIDA (Zero coupling externo) |
| **company_profile**| `audit`, `documents` | `auth_dependencies`, `principal` | Domain -> Shared Infrastructure | VÁLIDA (`asset_service.py` persiste logos en storage de documentos) |
| **cost_centers** | `procurement` | `auth_dependencies`, `principal` | Cross-Domain Persistence | DEUDA P3 (`service.py` importa modelo de requisición para comprobar borrado seguro) |
| **documents** | `audit`, `company_profile` | `auth_dependencies`, `principal` | Shared Service -> Domain | DEUDA P3 (`lifecycle_service.py` importa modelo de perfil para membretes) |
| **drivers** | `audit`, `partners` | `auth_dependencies`, `principal` | Domain -> Domain | VÁLIDA (`driver_service.py` valida asociación a transportista) |
| **files** | `audit` | `auth_dependencies`, `principal` | Standalone Shared Service | VÁLIDA (Gestor binario desacoplado) |
| **gate_control** | `documents`, `drivers`, `inbound` | `auth_dependencies`, `principal` | Domain -> Composite | VÁLIDA (Control de acceso orquesta vehículo, conductor y guía) |
| **inbound** | `audit`, `documents`, `drivers`, `files`, `partners`, `procurement`, `products`, `rbac`, `units`, `vehicle_verifications`, `vehicles` | `auth_dependencies`, `principal` | Composite Domain Orchestration | VÁLIDA (Recepción orquesta orden de compra, transportista, vehículo y balanza) |
| **integrations** | *Ninguno* | `dependencies` | External Gateway | VÁLIDA |
| **inventory** | `documents`, `inbound`, `units` | `auth_dependencies`, `principal`, `security` | Domain -> Domain & Shared | VÁLIDA (Ingreso a stock desde recepción y balance por unidades) |
| **organization** | *Ninguno* | `dependencies` | Master Domain | VÁLIDA |
| **partners** | `audit` | `auth_dependencies`, `principal` | Master Domain | VÁLIDA |
| **procurement** | `cost_centers`, `documents`, `files`, `products`, `units` | `auth_dependencies`, `principal` | Domain -> Master & Shared | VÁLIDA (Requisición valida producto, centro de costo y unidad) |
| **products** | `warehouses` | `auth_dependencies`, `principal` | Domain -> Master | VÁLIDA (Reglas de almacenamiento por categoría de producto) |
| **purchase_orders**| `partners`, `products` | `auth_dependencies`, `principal` | Domain -> Master | VÁLIDA |
| **rbac** | `audit`, `security` | `auth_dependencies`, `principal` | Security Domain | VÁLIDA |
| **routes_module** | *Ninguno* | `dependencies` | Standalone Shared Service | VÁLIDA |
| **ruc** | `audit`, `partners` | `auth_dependencies`, `principal` | Integration Domain | VÁLIDA |
| **security** | *Ninguno* | `auth_dependencies`, `principal` | Security Engine | VÁLIDA |
| **shared** | *Ninguno* | *Ninguno* | Primitive Library | VÁLIDA |
| **units** | `products` | `auth_dependencies`, `principal` | Master Domain | VÁLIDA |
| **vehicle_verifications**| `audit`, `vehicles` | `auth_dependencies`, `principal` | Domain -> Domain | VÁLIDA |
| **vehicles** | `audit`, `partners`, `units` | `auth_dependencies`, `principal` | Domain -> Master | VÁLIDA |
| **warehouses** | `audit`, `documents` | `auth_dependencies`, `principal` | Master -> Shared | VÁLIDA (Generación de etiquetas QR y documentos de ubicación) |

---

## 2. Evidencia Estricta de Ciclos de Dependencia (AST Cycle Analysis)

El análisis estático del árbol de importaciones detectó **2 ciclos bidireccionales**:

```mermaid
graph LR
    A["company_profile"] <-->|Bidireccional| B["documents"]
    C["cost_centers"] <-->|Bidireccional| D["procurement"]
```

### Detalle y Evidencia de Código:

#### 1. `company_profile` ↔ `documents`
- **Dirección A → B:**
  - Archivo: `backend/app/modules/logistics/company_profile/asset_service.py`
  - Línea de import: `from app.modules.logistics.documents.infrastructure.storage import DocumentArtifactStorage`
- **Dirección B → A:**
  - Archivo: `backend/app/modules/logistics/documents/application/lifecycle_service.py`
  - Línea de import: `from app.modules.logistics.company_profile.models import CompanyProfileModel`
- **Diagnóstico:** Acoplamiento bidireccional leve resuelto mediante imports diferidos a nivel de función (`lazy import`). No produce errores en tiempo de ejecución.
- **Clasificación:** `P3 - Deuda Arquitectónica`.

#### 2. `cost_centers` ↔ `procurement`
- **Dirección C → D:**
  - Archivo: `backend/app/modules/logistics/cost_centers/service.py`
  - Línea de import: `from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import PurchaseRequisitionModel`
- **Dirección D → C:**
  - Archivo: `backend/app/modules/logistics/procurement/requisitions/application/services/requisition_service.py`
  - Línea de import: `from app.modules.logistics.cost_centers.models import CostCenterModel`
- **Diagnóstico:** Dependencia cruzada de modelos ORM para comprobación de integridad referencial antes de borrado y validación antes de creación.
- **Clasificación:** `P3 - Deuda Arquitectónica`.

---

## 3. Dependencia de Componentes Transversales

```mermaid
graph TD
    subgraph Dominios
        Proc["Compras / Procurement"]
        Inb["Recepción / Inbound"]
        Inv["Inventario / Inventory"]
        Trans["Transporte / Vehicles / Drivers"]
        Part["Maestros / Partners / Warehouses"]
    end

    subgraph Servicios Transversales
        Doc["Documents Engine"]
        Fil["Files Storage & Evidence"]
        Aud["Audit Events"]
        Rout["Routes Module"]
        Integ["Integrations & RUC"]
        Sec["Security & RBAC & Principal"]
    end

    Proc --> Doc
    Proc --> Fil
    Proc --> Aud
    Proc --> Sec

    Inb --> Doc
    Inb --> Fil
    Inb --> Aud
    Inb --> Sec
    Inb --> Integ

    Inv --> Doc
    Inv --> Aud
    Inv --> Sec

    Trans --> Doc
    Trans --> Rout
    Trans --> Aud
    Trans --> Sec

    Part --> Integ
    Part --> Aud
    Part --> Sec
```
