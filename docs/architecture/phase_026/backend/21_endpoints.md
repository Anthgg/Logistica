# 21 — Especificación de Endpoints REST OpenAPI (`/api/logistics/ruc`)

## 1. Resumen de Endpoints

| Método | Ruta HTTP | Permiso RBAC Required | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/logistics/ruc/lookup/{ruc}` | `logistics.ruc_lookup.read` | Consulta unificada de RUC con procedencia y anexos. |
| `POST` | `/api/logistics/ruc/datasets/import` | `logistics.ruc_imports.execute` | Inicia un trabajo de importación manual de padrón. |
| `GET` | `/api/logistics/ruc/datasets/status` | `logistics.ruc_lookup.read` | Estado de las versiones e ingestas de datasets. |
| `POST` | `/api/logistics/ruc/datasets/{id}/activate` | `logistics.ruc_datasets.activate` | Activación manual de una versión de dataset (Step-Up). |
| `POST` | `/api/logistics/ruc/datasets/{id}/rollback` | `logistics.ruc_datasets.activate` | Rollback manual a una versión previa (Step-Up). |
| `POST` | `/api/logistics/ruc/verifications/assisted` | `logistics.ruc_assisted.create` | Registrar verificación asistida por operador. |
| `POST` | `/api/logistics/ruc/conflicts/{id}/resolve` | `logistics.ruc_conflicts.resolve` | Resolver un conflicto de datos de RUC. |

---

## 2. Detalle de Endpoint Principal (`GET /api/logistics/ruc/lookup/{ruc}`)

### Solicitud:
```http
GET /api/logistics/ruc/lookup/20100070970 HTTP/1.1
Host: api.erp.empresa.com
Authorization: Bearer <JWT_TOKEN>
```

### Respuesta HTTP 200 OK:
```json
{
  "ruc": "20100070970",
  "normalized_ruc": "20100070970",
  "legal_name": "EMPRESA DE PRUEBA SAC",
  "taxpayer_status": "ACTIVE",
  "domicile_condition": "HABIDO",
  "ubigeo_code": "150101",
  "annex_addresses": [
    {
      "ubigeo_code": "150101",
      "address_raw": "AV. JAVIER PRADO ESTE 123",
      "address_normalized": "AV JAVIER PRADO ESTE 123"
    }
  ],
  "source_type": "OFFICIAL_REDUCED_REGISTRY",
  "confidence_level": "HIGH",
  "staleness_level": "FRESH",
  "dataset_version_id": "8f3b7d12-4a5c-4e89-9123-112233445566",
  "fetched_at": "2026-07-28T00:00:00Z"
}
```
