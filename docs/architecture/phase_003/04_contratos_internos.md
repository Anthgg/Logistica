# 04. Contratos Internos

## Documents

| Protocol | Método | Entrada | Salida |
|----------|--------|---------|--------|
| `DocumentRenderer` | `render()` | `DocumentSnapshot` | `bytes` |
| `DocumentStorage` | `save()` | `bytes, DocumentSnapshot` | `StoredDocument` |
| `DocumentStorage` | `retrieve()` | `UUID` | `bytes` |
| `DocumentNumberGenerator` | `next_number()` | `DocumentType` | `DocumentNumber` |
| `DocumentSnapshotRepository` | `save()` | `DocumentSnapshot` | `DocumentSnapshot` |
| `DocumentSnapshotRepository` | `get_by_id()` | `UUID` | `DocumentSnapshot \| None` |
| `DocumentVerificationService` | `verify()` | `str` | `bool` |

## Routes

| Protocol | Método | Entrada | Salida |
|----------|--------|---------|--------|
| `DirectionsProvider` | `calculate()` | `RouteRequest` | `RouteResult` |
| `GeocodingProvider` | `geocode()` | `GeocodeRequest` | `GeocodeResult` |
| `MapMatchingProvider` | `match()` | `MapMatchRequest` | `MapMatchResult` |
| `RouteRepository` | `save()` | `RouteResult, UUID` | `UUID` |
| `RouteCalculationService` | `calculate_route()` | `RouteRequest` | `RouteResult` |

## Files

| Protocol | Método | Entrada | Salida |
|----------|--------|---------|--------|
| `FileStorage` | `save()` | `SaveFileRequest` | `StoredFile` |
| `FileStorage` | `read()` | `UUID` | `bytes` |
| `FileMetadataRepository` | `get_by_id()` | `UUID` | `FileMetadata \| None` |
| `FileValidator` | `validate()` | `bytes, str, str` | `bool` |
| `FileHashService` | `compute_sha256()` | `bytes` | `str` |
| `SignedUrlProvider` | `generate()` | `UUID, int` | `SignedUrl` |

## Audit

| Protocol | Método | Entrada | Salida |
|----------|--------|---------|--------|
| `AuditEventWriter` | `write()` | `AuditEvent` | `None` |
| `AuditEventReader` | `list_for_resource()` | `str, UUID` | `list[AuditEvent]` |
| `AuditContextProvider` | `current_context()` | — | `dict[str, str \| None]` |
| `AuditSerializer` | `serialize()` | `AuditEvent` | `dict[str, object]` |

## Integrations

| Protocol | Método | Entrada | Salida |
|----------|--------|---------|--------|
| `IntegrationAdapter` | `execute()` | `IntegrationRequest` | `IntegrationResponse` |
| `IntegrationRegistry` | `get_adapter()` | `IntegrationProvider` | `IntegrationAdapter \| None` |
| `IntegrationCache` | `get()` | `str` | `dict \| None` |
| `IntegrationCache` | `set()` | `str, dict, int` | `None` |

Todos los contratos usan `typing.Protocol` — no dependen de FastAPI ni SQLAlchemy.