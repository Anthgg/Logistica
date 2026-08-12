# 02 — Arquitectura del Módulo RUC (`app/modules/logistics/ruc/`)

## 1. Principios de Diseño por Capas (Clean Architecture)

El módulo RUC se ubica dentro del subdominio de Logística (`app/modules/logistics/ruc/`) y sigue una arquitectura en capas estrictamente desacoplada:

```
app/modules/logistics/ruc/
├── domain/
│   ├── errors/
│   │   └── exceptions.py
│   ├── services/
│   │   └── policies.py
│   └── value_objects/
│       └── enums.py
├── application/
│   └── services/
│       ├── import_service.py
│       ├── lookup_service.py
│       └── verification_service.py
├── infrastructure/
│   ├── cache/
│   │   └── ruc_cache.py
│   ├── importers/
│   │   └── safe_downloader.py
│   ├── jobs/
│   │   └── run_ruc_import_job.py
│   ├── parsers/
│   │   └── ruc_parser.py
│   ├── persistence/
│   │   └── models.py
│   └── providers/
│       └── ruc_provider.py
└── presentation/
    ├── routes/
    │   └── router.py
    └── schemas/
        └── dto.py
```

---

## 2. Definición de Capas

### 2.1. Capa de Dominio (`domain/`)
Contiene los objetos de valor, enums, excepciones de negocio y políticas puras sin dependencias de infraestructura:
- **`enums.py`**: `RucSourceType`, `TaxpayerStatus`, `DomicileCondition`, `StalenessLevel`, `ConfidenceLevel`.
- **`exceptions.py`**: Excepciones domain-driven como `RucInvalidError`, `RucNotFoundError`, `RucImportAnomalousRowCountError`, `RucImportZipBombError`.
- **`policies.py`**: `RucStalenessPolicy` (cálculo de vigencia de datos), `RucConfidencePolicy` (determinación del grado de confianza de la fuente), `RucFieldProvenanceBuilder`.

### 2.2. Capa de Aplicación (`application/`)
Orquesta las operaciones de uso del sistema coordinando repositorios, servicios de infraestructura y eventos de auditoría:
- **`RucLookupService`**: Orquesta la consulta unificada de RUC (Cache L1/L2 -> Padrón DB -> Enriquecimiento Fallback).
- **`RucRegistryImportService`**: Orquesta la ingesta de padrones, control de anomalías y activación atómica.
- **`RucAssistedVerificationService`**: Gestiona el flujo de verificación manual asistida con regla de 4 ojos.
- **`BusinessPartnerRucIntegrationService`**: Vincula la verificación de RUC con el Maestro de Socios Comerciales (`business_partners`).

### 2.3. Capa de Infraestructura (`infrastructure/`)
Implementa el acceso a datos, caché, comunicación HTTP y tareas en segundo plano:
- **`RucLookupCache`**: Gestión de caché L1 en memoria y L2 Redis aislada por versión de dataset.
- **`SafeZipDownloader` / `SafeZipExtractor`**: Descarga HTTPS segura con lista blanca de dominios y extracción anti ZIP-bomb.
- **`RucRegistryParser`**: Parser streaming de alto rendimiento para archivos delimitados.
- **`models.py`**: Modelos ORM SQLAlchemy vinculados a la migración `q280110026dc`.
- **`ruc_provider.py`**: Adaptadores `NoOpRucProvider` y `FakeRucProvider`.

### 2.4. Capa de Presentación (`presentation/`)
Expone la API REST mediante FastAPI y Pydantic v2:
- **`router.py`**: Endpoints bajo la ruta `/api/logistics/ruc`.
- **`dto.py`**: DTOs de solicitud y respuesta con validaciones estrictas y esquemas OpenAPI.
