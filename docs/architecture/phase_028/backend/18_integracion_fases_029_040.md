# Contrato de Integración con Fase 029 (Conductores) y Fases de Control de Acceso / Despacho (040+)

## 1. Descripción General

La **Fase 028 (Integración de Verificaciones Vehiculares)** se posiciona en la capa de servicios de cumplimiento del ERP. Expone contratos limpios y desacoplados para integrarse con:
1. **Fase 029 (Maestro de Conductores)**: Verificación conjunta de la dupla Vehículo-Conductor.
2. **Fase 041 (Control de Acceso en Garita / Peso en Balanza)**: Validación en tiempo real al momento de la llegada física del vehículo a planta.
3. **Fase 042 (Despacho de Carga / Emisión de Guías de Remisión)**: Bloqueo preventivo de orden de salida ante faltas de verificación.

---

## 2. Diagrama de Acoplamiento entre Fases Logísticas

```mermaid
graph LR
    subgraph Fase 027
        V[VehicleModel]
    end

    subgraph Fase 028
        VER[VehicleVerificationComplianceResolver]
    end

    subgraph Fase 029
        D[DriverModel & Licenses]
    end

    subgraph Fase 041
        GAR[Gate Access Control / Scale]
    end

    subgraph Fase 042
        DISP[Cargo Dispatch & Waybills]
    end

    V --> VER
    D --> GAR
    VER -->|resolve_compliance()| GAR
    VER -->|resolve_compliance()| DISP
    GAR -->|Si status == BLOCKED| DENY[Denegar Ingreso]
    DISP -->|Si status == BLOCKED| BLOCK[Bloquear Emisión Guía Remisión]
```

---

## 3. Contrato de Integración con Fase 029 (Conductores)

El módulo de Conductores (Fase 029) requiere validar si la unidad asignada a un conductor cuenta con verificación SUNARP y SOAT vigente antes de autorizar la orden de servicio.

### Interfaz de Vinculación Vehículo-Conductor
```python
def validate_vehicle_driver_pair_compliance(
    db: Session, 
    vehicle_id: UUID, 
    driver_id: UUID
) -> Dict[str, Any]:
    # 1. Obtener dictamen vehicular (Fase 028)
    vehicle_status = VehicleVerificationComplianceResolver.resolve_compliance(db, vehicle_id)
    
    # 2. Obtener dictamen de licencia del conductor (Fase 029)
    driver_status = DriverLicenseResolver.resolve_compliance(db, driver_id)
    
    is_duo_authorized = vehicle_status["is_authorized"] and driver_status["is_authorized"]
    
    return {
        "is_authorized": is_duo_authorized,
        "vehicle_compliance": vehicle_status,
        "driver_compliance": driver_status,
        "can_assign_trip": is_duo_authorized
    }
```

---

## 4. Contrato de Integración con Garita (Fase 041) y Despacho (Fase 042)

Los sistemas de balanza y portón de garita consumen el endpoint `/api/v1/logistics/vehicle-verifications/compliance-status/{vehicle_id}`.

### Criterios de Decisión en Garita / Despacho

| Estado Devuelto por Fase 028 | Comportamiento en Garita (Fase 041) | Comportamiento en Despacho (Fase 042) |
|---|---|---|
| `AUTHORIZED_FOR_DISPATCH` | Apertura de talanquera y balanza autorizada. | Emisión automática de Guía de Remisión Electrónica. |
| `CONDITIONALLY_AUTHORIZED` | Ingreso permitido con registro de aviso en pantalla de garita. | Permite despacho previa confirmación visual de supervisor. |
| `BLOCKED_NON_COMPLIANT` | **Apertura Denegada**. Pantalla roja con detalle de faltas. | **Bloqueo de Sistema**. Inhabilitación del botón de despacho. |
