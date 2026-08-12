# 17 — Verificación Manual Oficial Asistida (`RucAssistedVerificationService`)

## 1. Flujo de Verificación Asistida por Operador

Cuando un contribuyente de reciente creación no aparece en el padrón masivo ni en los proveedores autorizados, un operador del equipo legal/compras puede realizar una consulta manual directa en la plataforma interactiva oficial de SUNAT desde su navegador web y registrar la verificación en el ERP.

```mermaid
sequenceDiagram
    autonumber
    participant Op as Operador (Compras/Legal)
    participant ERP as RucAssistedVerificationService
    participant DB as PostgreSQL Database
    participant Sup as Supervisor (Regla 4 Ojos)

    Op->>ERP: POST /api/logistics/ruc/verifications/assisted (RUC, Evidencia PDF/Link)
    ERP->>DB: INSERT INTO ruc_assisted_verifications (result='PENDING_APPROVAL')
    ERP-->>Op: Verificación registrada ID (Pendiente Aprobación)
    
    Sup->>ERP: POST /api/logistics/ruc/verifications/assisted/{id}/approve
    ERP->>ERP: Validar approved_by != reviewed_by (Regla 4 Ojos)
    ERP->>DB: UPDATE ruc_assisted_verifications SET result='MATCH_CONFIRMED', approved_at=NOW()
    ERP-->>Sup: Aprobación Confirmada (Confianza MEDIUM)
```

---

## 2. Restricción Estricta de Cuatro Ojos (4-Eyes Rule)

El usuario que aprueba la verificación asistida (`approved_by`) debe ser strictly diferente del operador que la registró (`reviewed_by`). Esto previene fraudes en el alta de proveedores no verificados.

```python
if verification.reviewed_by == current_user_id:
    raise RucAssistedApprovalError("El usuario aprobador debe ser diferente del operador que registró la evidencia.")
```
