# 15 — Evaluador de Cumplimiento Documental (`DriverDocumentComplianceResolver`)

## Algoritmo de Evaluación de Cumplimiento

El servicio `DriverDocumentComplianceResolver` determina de forma pura, determinista y reutilizable el campo `compliance_status` (`COMPLIANT`, `WARNING`, `NON_COMPLIANT`, `EXPIRED`) del conductor.

---

## Reglas de Evaluación por Prioridad

1. **`EXPIRED`**: Si cualquier documento obligatorio (DNI, Licencia Primaria, Aptitud Médica o Hazmat si aplica) se encuentra vencido (`expires_at < current_date`).
2. **`NON_COMPLIANT`**: Si falta algún documento obligatorio requerido según la matriz de exigencias o si la Licencia Primaria está en estado `SUSPENDED` / `REVOKED`.
3. **`WARNING`**: Si todos los documentos obligatorios están vigentes, pero uno o más vencerán dentro de la ventana de advertencia (`warning_buffer_days`, por defecto 30 días).
4. **`COMPLIANT`**: Si todos los documentos obligatorios existen, están verificados y sus fechas de vencimiento superan la ventana de advertencia.

---

## Código Python del Resolver

```python
from datetime import date, timedelta
from typing import List, Tuple
from app.models.logistics.driver import DriverModel, DriverComplianceStatus
from app.models.logistics.driver_document_requirement import DriverDocumentRequirementModel

class DriverDocumentComplianceResolver:

    @classmethod
    def resolve_compliance(
        cls,
        driver: DriverModel,
        requirements: List[DriverDocumentRequirementModel],
        evaluation_date: date = None
    ) -> Tuple[DriverComplianceStatus, List[str]]:
        """
        Evalúa el estado de cumplimiento documental del conductor frente a una lista de requisitos.
        Retorna la tupla (DriverComplianceStatus, list_of_reasons).
        """
        if evaluation_date is None:
            evaluation_date = date.today()
            
        reasons: List[str] = []
        has_expired = False
        has_missing = False
        has_warning = False
        
        # 1. Evaluar Licencia Primaria (Siempre Obligatoria)
        primary_license = next((lic for lic in driver.licenses if lic.is_primary), None)
        if not primary_license:
            has_missing = True
            reasons.append("Falta la Licencia de Conducir primaria.")
        else:
            if primary_license.expires_at < evaluation_date:
                has_expired = True
                reasons.append(f"La Licencia de Conducir {primary_license.masked_license_number} venció el {primary_license.expires_at}.")
            elif primary_license.expires_at <= evaluation_date + timedelta(days=30):
                has_warning = True
                reasons.append(f"La Licencia de Conducir vencerá en menos de 30 días ({primary_license.expires_at}).")
            if primary_license.status in ["SUSPENDED", "REVOKED"]:
                has_missing = True
                reasons.append(f"La Licencia de Conducir está {primary_license.status.value}.")

        # 2. Evaluar Documento de Identidad Primario (DNI/CE)
        primary_identity = next((doc for doc in driver.identity_documents if doc.is_primary), None)
        if not primary_identity:
            has_missing = True
            reasons.append("Falta el Documento de Identidad primario (DNI/CE).")
        else:
            if primary_identity.expires_at and primary_identity.expires_at < evaluation_date:
                has_expired = True
                reasons.append(f"El Documento de Identidad {primary_identity.masked_document_number} venció el {primary_identity.expires_at}.")

        # 3. Evaluar Requisitos Documentales Adicionales según Matriz
        for req in requirements:
            if not req.is_mandatory or not req.is_active:
                continue
                
            matching_docs = [d for d in driver.documents if d.document_type == req.document_type_required]
            if not matching_docs:
                has_missing = True
                reasons.append(f"Falta el documento obligatorio de tipo '{req.document_type_required}'.")
                continue
                
            valid_doc = next((d for d in matching_docs if d.is_valid), None)
            if not valid_doc:
                has_expired = True
                reasons.append(f"El documento '{req.document_type_required}' se encuentra vencido.")
            else:
                if valid_doc.expires_at and valid_doc.expires_at <= evaluation_date + timedelta(days=req.warning_buffer_days):
                    has_warning = True
                    reasons.append(f"El documento '{req.document_type_required}' vencerá el {valid_doc.expires_at}.")

        # Resolución Final por Prioridad
        if has_expired:
            return DriverComplianceStatus.EXPIRED, reasons
        if has_missing:
            return DriverComplianceStatus.NON_COMPLIANT, reasons
        if has_warning:
            return DriverComplianceStatus.WARNING, reasons

        return DriverComplianceStatus.COMPLIANT, ["Todos los documentos obligatorios están vigentes."]
```
