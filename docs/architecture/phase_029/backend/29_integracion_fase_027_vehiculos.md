# Contrato de Integración con Fase 027 (Maestro de Vehículos)

## Propósito
Define la integración cualitativa entre el Maestro de Conductores (Fase 029) y el Maestro de Vehículos (Fase 027) mediante el evaluador de compatibilidad.

## Evaluador `EvaluateDriverVehicleCompatibility`
- Valida que la categoría de licencia activa del conductor autorice la clase/tipo del vehículo de Fase 027 (ej. `C3_TRUCK`, `SEMI_TRAILER`).
- Consulta la tabla `driver_license_vehicle_type_rules`.
- No modifica ningún registro vehicular ni de conductor.
- No crea despachos ni asignaciones operativas en esta fase.
