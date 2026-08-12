# 16 — Evaluador de Elegibilidad Operativa (`DriverOperationalEligibilityResolver`)

## Algoritmo de Resolución de Elegibilidad

Mientras que el cumplimiento documental (`DriverDocumentComplianceResolver`) se enfoca exclusivamente en la validez de papeles y fechas, el **`DriverOperationalEligibilityResolver`** dictamina si el conductor está efectivamente autorizado para ser asignado a despachos o rutas de transporte en tiempo real.

---

## Matriz de Transición de Elegibilidad

| `lifecycle_status` | `compliance_status` | ¿Restricciones Operativas Activas? | Estado Final `eligibility_status` |
|---|---|---|---|
| CUALQUIERA | CUALQUIERA | Sí (`TEMPORARY_SUSPENSION` / `PERMANENT_BLOCK`) | **`INELIGIBLE`** |
| `DRAFT` / `SUSPENDED` / `INACTIVE` | CUALQUIERA | CUALQUIERA | **`INELIGIBLE`** |
| `ACTIVE` | `NON_COMPLIANT` / `EXPIRED` | No | **`INELIGIBLE`** |
| `ACTIVE` | `WARNING` | No (Solo advertencias menores) | **`RESTRICTED`** |
| `ACTIVE` | `COMPLIANT` | No | **`ELIGIBLE`** |

---

## Código Python del Resolver

```python
from typing import Tuple, List
from datetime import datetime, timezone
from app.models.logistics.driver import (
    DriverModel, 
    DriverLifecycleStatus, 
    DriverComplianceStatus, 
    DriverEligibilityStatus
)

class DriverOperationalEligibilityResolver:

    @classmethod
    def resolve_eligibility(cls, driver: DriverModel) -> Tuple[DriverEligibilityStatus, List[str]]:
        """
        Evalúa determinísticamente la elegibilidad operativa del conductor combinando
        su ciclo de vida, cumplimiento documental y sanciones/restricciones operativas.
        """
        reasons: List[str] = []
        now = datetime.now(timezone.utc)

        # 1. Verificar Sanciones o Restricciones Operativas Activas
        active_locks = [
            r for r in driver.operational_restrictions 
            if r.is_active and r.severity in ["TEMPORARY_SUSPENSION", "PERMANENT_BLOCK"]
            and (r.end_date is None or r.end_date > now)
        ]
        if active_locks:
            lock_reasons = [f"Bloqueo activo: {lock.reason} (Tipo: {lock.restriction_type.value})" for lock in active_locks]
            return DriverEligibilityStatus.INELIGIBLE, lock_reasons

        # 2. Verificar Ciclo de Vida del Conductor
        if driver.lifecycle_status != DriverLifecycleStatus.ACTIVE:
            return DriverEligibilityStatus.INELIGIBLE, [
                f"El ciclo de vida del conductor está en '{driver.lifecycle_status.value}'. Debe estar en 'ACTIVE'."
            ]

        # 3. Evaluar Estado de Cumplimiento Documental
        if driver.compliance_status in [DriverComplianceStatus.NON_COMPLIANT, DriverComplianceStatus.EXPIRED]:
            return DriverEligibilityStatus.INELIGIBLE, [
                f"El estado de cumplimiento documental es '{driver.compliance_status.value}'."
            ]

        if driver.compliance_status == DriverComplianceStatus.WARNING:
            return DriverEligibilityStatus.RESTRICTED, [
                "Habilitado con restricciones por documentos próximos a vencer (Estado WARNING)."
            ]

        # 4. Elegibilidad Completa
        return DriverEligibilityStatus.ELIGIBLE, ["Conductor totalmente elegible para asignación operativa."]
```

---

## Recálculo Síncrono y Eventos de Cambio de Estado

Cada vez que se ejecuta una modificación en licencias, documentos o sanciones de un conductor:
1. El servicio invoca a `DriverDocumentComplianceResolver.resolve_compliance()`.
2. Luego invoca a `DriverOperationalEligibilityResolver.resolve_eligibility()`.
3. Si el `eligibility_status` cambia (ejemplo: de `ELIGIBLE` a `INELIGIBLE`), se dispara de inmediato una notificación al bus de eventos de la plataforma para cancelar o reasignar despachos en tránsito si fuera necesario.
