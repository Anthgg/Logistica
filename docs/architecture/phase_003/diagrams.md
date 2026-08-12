# Diagramas Mermaid — Fase 003

## 1. Arquitectura General

```mermaid
graph TB
    subgraph "App existente"
        API[api/router.py]
        AUTH[dependencies/auth.py]
        CSRF[dependencies/csrf.py]
        DB[database/session.py]
    end

    subgraph "Dominio Logístico"
        LR[logistics/router.py]
        DEP[logistics/dependencies.py]
        EXC[logistics/exceptions.py]
        CONST[logistics/constants.py]

        subgraph "Submódulos"
            DOC[documents/]
            RT[routes_module/]
            FIL[files/]
            AUD[audit/]
            INT[integrations/]
        end
    end

    API -->|include_router| LR
    LR --> DOC
    LR --> RT
    LR --> FIL
    LR --> AUD
    LR --> INT
    DEP --> AUTH
    DEP --> CSRF
    DOC -->|contrato| FIL
    DOC -->|contrato| AUD
    RT -->|contrato| INT
```

## 2. Capas del Dominio Logístico

```mermaid
graph TB
    subgraph "Por submódulo"
        API_LAYER[API — FastAPI router]
        APP_LAYER[Application — servicios]
        DOM_LAYER[Domain — entidades, Protocols]
        INFRA_LAYER[Infrastructure — implementaciones]

        API_LAYER --> APP_LAYER
        APP_LAYER --> DOM_LAYER
        INFRA_LAYER --> DOM_LAYER
    end
```

## 3. Dependencias entre Módulos

```mermaid
graph LR
    DOC[documents] -->|FileStorage| FIL[files]
    DOC -->|AuditEventWriter| AUD[audit]
    RT[routes_module] -->|IntegrationAdapter| INT[integrations]
    FIL ~~~ AUD
    FIL ~~~ INT
```

## 4. Registro de Routers

```mermaid
graph TB
    MAIN[app/main.py]
    ROUTER[app/api/router.py]
    LOGISTICS[app/modules/logistics/router.py]

    MAIN -->|prefix=/api| ROUTER
    ROUTER -->|include_router| LOGISTICS

    LOGISTICS -->|prefix=/documents| DOC_R[documents/api/router.py]
    LOGISTICS -->|prefix=/routes| RT_R[routes_module/api/router.py]
    LOGISTICS -->|prefix=/files| FIL_R[files/api/router.py]
    LOGISTICS -->|prefix=/audit| AUD_R[audit/api/router.py]
    LOGISTICS -->|prefix=/integrations| INT_R[integrations/api/router.py]
```

## 5. Flujo API → Aplicación → Dominio → Infraestructura

```mermaid
graph LR
    REQ[HTTP Request] --> API[API Layer]
    API --> APP[Application Service]
    APP --> DOM[Domain Contract/Protocol]
    DOM -.->|implementado por| INFRA[Infrastructure]
    INFRA --> DB[(PostgreSQL)]
    INFRA --> EXT[Servicio externo]
```

## 6. Integración con Autenticación

```mermaid
graph TB
    REQ[Request] --> CSRF_MW[CSRF verify]
    CSRF_MW --> SESSION_DEP[get_current_session]
    SESSION_DEP --> LOG_DEP[get_logistics_current_user]
    LOG_DEP --> ROUTE[Logistics endpoint]
    ROUTE --> PERM[require_logistics_permission]
    PERM --> ACTIVE[require_active_user]
```

## 7. Adaptadores de Proveedores Externos

```mermaid
graph TB
    subgraph "Dominio (contratos)"
        DP[DirectionsProvider]
        GP[GeocodingProvider]
        IA[IntegrationAdapter]
    end

    subgraph "Infraestructura (futura)"
        OSRM[OSRM Adapter]
        ORS[openrouteservice Adapter]
        SUNAT[SUNAT Adapter]
        SMS[SMS Adapter]
    end

    DP -.-> OSRM
    DP -.-> ORS
    GP -.-> ORS
    IA -.-> SUNAT
    IA -.-> SMS
```

## 8. Flujo Futuro de Auditoría

```mermaid
sequenceDiagram
    participant API
    participant APP as Application
    participant AUDIT as AuditEventWriter
    participant EXISTING as AuditService existente

    API->>APP: Ejecuta operación logística
    APP->>AUDIT: write(AuditEvent)
    AUDIT->>EXISTING: record(event_type, metadata)
    EXISTING->>DB: INSERT audit_log
```