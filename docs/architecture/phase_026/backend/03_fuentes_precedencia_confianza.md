# 03 — Fuentes de Datos, Jerarquía de Precedencia y Niveles de Confianza

## 1. Catálogo de Fuentes de Datos (`RucSourceType`)

El sistema clasifica el origen de los datos de contribuyentes en cuatro tipos jerárquicos:

```python
class RucSourceType(str, Enum):
    OFFICIAL_REDUCED_REGISTRY = "OFFICIAL_REDUCED_REGISTRY"  # Padrón Reducido SUNAT
    AUTHORIZED_PROVIDER = "AUTHORIZED_PROVIDER"              # API REST de Proveedor Homologado
    ASSISTED_OFFICIAL_REVIEW = "ASSISTED_OFFICIAL_REVIEW"    # Verificación manual aprobada (4 ojos)
    MANUAL_DECLARATION = "MANUAL_DECLARATION"                # Declaración del socio sin verificar
```

---

## 2. Jerarquía de Precedencia y Reglas de Confianza

Cuando existen múltiples fuentes de datos disponibles para un mismo RUC, el sistema aplica la jerarquía definida en `RucConfidencePolicy`:

| Prioridad | Fuente (`RucSourceType`) | Nivel de Confianza | Criterio de Selección |
| :---: | :--- | :---: | :--- |
| **1** | `OFFICIAL_REDUCED_REGISTRY` | `HIGH` | Máxima autoridad tributaria (SUNAT). Prevalece para Razón Social, Estado y Condición. |
| **2** | `AUTHORIZED_PROVIDER` | `HIGH` / `MEDIUM` | API con SLA contractual. Se utiliza en caso de RUCs de reciente creación no presentes en el padrón mensual. |
| **3** | `ASSISTED_OFFICIAL_REVIEW` | `MEDIUM` | Verificación manual documentada con evidencia y aprobada por un segundo usuario. |
| **4** | `MANUAL_DECLARATION` | `LOW` | Dato ingresado por el usuario/socio comercial sin contraste de fuente externa. |

---

## 3. Procedencia por Campo (`RucFieldProvenance`)

Dado que diferentes campos de un contribuyente pueden provenir de fuentes distintas (por ejemplo, Razón Social del Padrón y Dirección Anexa de un Proveedor), el DTO de respuesta incluye procedencia atómica por campo:

```json
{
  "ruc": "20100070970",
  "legal_name": "EMPRESA DE PRUEBA SAC",
  "provenance": {
    "legal_name": {
      "source_type": "OFFICIAL_REDUCED_REGISTRY",
      "confidence_level": "HIGH",
      "dataset_version_id": "8f3b7d12-4a5c-4e89-9123-112233445566",
      "updated_at": "2026-07-28T00:00:00Z"
    },
    "taxpayer_status": {
      "source_type": "OFFICIAL_REDUCED_REGISTRY",
      "confidence_level": "HIGH",
      "dataset_version_id": "8f3b7d12-4a5c-4e89-9123-112233445566",
      "updated_at": "2026-07-28T00:00:00Z"
    }
  }
}
```
