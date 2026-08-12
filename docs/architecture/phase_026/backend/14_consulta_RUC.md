# 14 — Flujo de Consulta Unificada de RUC (`RucLookupService`)

## 1. Algoritmo Paso a Paso de Consulta

El servicio `RucLookupService` implementa el flujo unificado de resolución de consultas de contribuyentes:

```mermaid
flowchart TD
    A[Inicio: Consulta RUC 11 dígitos] --> B{Validar Sintaxis PeruvianRucValidator}
    B -- Inválido --> C[Raise RucInvalidError 400]
    B -- Válido --> D[Obtener Dataset Version ACTIVE]
    D --> E{Consultar RucLookupCache}
    E -- HIT --> F[Retornar DTO desde Caché <15ms]
    E -- MISS --> G[Consultar DB ruc_registry_entries + Annexes]
    G -- Encontrado --> H[Guardar en Caché L1/L2]
    H --> I[Retornar RucLookupResponseDTO]
    G -- No Encontrado --> J{Proveedor Autorizado Configurado?}
    J -- Sí --> K[Invocar RucEnrichmentProvider]
    K -- Encontrado --> L[Guardar en DB / Caché & Retornar]
    K -- Fallo / No Encontrado --> M[Guardar Negative Cache & Raise RucNotFoundError 404]
    J -- No --> M
```

---

## 2. Estructura de Respuesta DTO

```python
class RucLookupResponseDTO(BaseModel):
    ruc: str
    normalized_ruc: str
    legal_name: str
    taxpayer_status: TaxpayerStatus
    domicile_condition: DomicileCondition
    ubigeo_code: str | None
    annex_addresses: list[RucAnnexAddressDTO] = []
    
    source_type: RucSourceType
    confidence_level: ConfidenceLevel
    staleness_level: StalenessLevel
    dataset_version_id: UUID | None
    fetched_at: datetime
```
