# 17 — Detección de Duplicados (`DriverDuplicateDetectionService`)

## Propósito y Prevención de Duplicidad

En operaciones logísticas multisitio con registro descentralizado de conductores (distintos centros de distribución o transportistas cargando choferes), es frecuente el intento de registrar nuevamente a un conductor existente. 

El servicio **`DriverDuplicateDetectionService`** implementa un **algoritmo probabilístico y por coincidencias exactas/parciales** para identificar posibles duplicados ANTES o DESPUÉS de la creación, emitiendo alertas sin ejecutar fusiones automáticas destructivas (evitando pérdida de datos históricos o auditoría).

---

## Criterios de Ponderación de Duplicidad

| Criterio | Coincidencia Evaluada | Puntaje (0-100) | Tipo |
|---|---|---|---|
| **Documento Identidad** | Mismo DNI/CE normalizado | **100 pts** | Exacto / Determinista |
| **Licencia de Conducir** | Mismo número de Licencia normalizado | **100 pts** | Exacto / Determinista |
| **Nombres y Apellidos** | Levenshtein Distance / Trigram Similarity | **30 pts** | Probabilístico |
| **Teléfono Móvil** | Mismo número E.164 normalizado | **20 pts** | Exacto |
| **Correo Electrónico** | Mismo correo normalizado | **15 pts** | Exacto |

### Niveles de Alerta de Duplicidad:
- **`CONFIRMED_DUPLICATE` (score >= 100)**: Bloquea la inserción automática (DNI o Licencia idéntica registrada).
- **`HIGH_PROBABILITY` (70 <= score < 100)**: Permite la creación pero genera una tarea de revisión administrativa.
- **`POSSIBLE_DUPLICATE` (40 <= score < 70)**: Advertencia informativa en UI.
- **`UNIQUE` (score < 40)**: Registro limpio.

---

## Código Python del Servicio

```python
from dataclasses import dataclass
from typing import List
import uuid
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.logistics.driver import DriverModel
from app.models.logistics.driver_identity_document import DriverIdentityDocumentModel
from app.models.logistics.driver_license import DriverLicenseModel

@dataclass
class DuplicateMatch:
    existing_driver_id: uuid.UUID
    existing_driver_code: str
    existing_display_name: str
    match_score: int
    matched_criteria: List[str]

class DriverDuplicateDetectionService:

    @classmethod
    async def detect_duplicates(
        cls,
        db: AsyncSession,
        organization_id: uuid.UUID,
        normalized_dni: str = None,
        normalized_license: str = None,
        first_name: str = None,
        last_name: str = None,
        normalized_phone: str = None
    ) -> List[DuplicateMatch]:
        """
        Evalúa el riesgo de duplicidad buscando contra el maestro de conductores de la organización.
        """
        matches = {}

        # 1. Búsqueda por DNI
        if normalized_dni:
            stmt = select(DriverIdentityDocumentModel).where(
                DriverIdentityDocumentModel.normalized_document_number == normalized_dni
            )
            res = await db.execute(stmt)
            for doc in res.scalars().all():
                if doc.driver.organization_id == organization_id:
                    d_id = doc.driver_id
                    matches[d_id] = matches.get(d_id, {"driver": doc.driver, "score": 0, "criteria": []})
                    matches[d_id]["score"] += 100
                    matches[d_id]["criteria"].append(f"Coincidencia exacta de DNI/CE ({doc.masked_document_number})")

        # 2. Búsqueda por Licencia
        if normalized_license:
            stmt = select(DriverLicenseModel).where(
                DriverLicenseModel.normalized_license_number == normalized_license
            )
            res = await db.execute(stmt)
            for lic in res.scalars().all():
                if lic.driver.organization_id == organization_id:
                    d_id = lic.driver_id
                    matches[d_id] = matches.get(d_id, {"driver": lic.driver, "score": 0, "criteria": []})
                    matches[d_id]["score"] += 100
                    matches[d_id]["criteria"].append(f"Coincidencia exacta de Licencia ({lic.masked_license_number})")

        # Convertir a lista de resultados ordenados por score descendente
        results = [
            DuplicateMatch(
                existing_driver_id=data["driver"].id,
                existing_driver_code=data["driver"].driver_code,
                existing_display_name=data["driver"].display_name,
                match_score=min(data["score"], 100),
                matched_criteria=data["criteria"]
            )
            for d_id, data in matches.items()
        ]
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results
```

---

## Política de No Autofusión (No Auto-Merge)

La plataforma **jamás ejecuta fusiones automáticas de registros de conductores**. Si un administrador confirma que dos registros pertenecen a la misma persona real:
1. Se selecciona el registro primario a conservar.
2. El registro secundario es marcado en `lifecycle_status = 'ARCHIVED'` con nota explicativa del ID unificado.
3. Se re-vinculan las licencias e historial de viajes hacia el registro primario preservando íntegramente la trazabilidad de auditoría.
