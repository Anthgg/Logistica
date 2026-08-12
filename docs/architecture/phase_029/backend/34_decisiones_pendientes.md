# Registro de Decisiones de Arquitectura (ADR) — Fase 029

## ADR 029-01: Desacoplamiento de Cuentas de Usuario y Registro Laboral
- **Decisión**: Los conductores no crean automáticamente usuarios en la plataforma ni registros en RRHH.
- **Estado**: Aprobado.

## ADR 029-02: Referencia Exclusiva por `file_reference_id` para Fotografías
- **Decisión**: No se almacena Base64 ni archivos públicos. No se realiza biometría ni reconocimiento facial.
- **Estado**: Aprobado.

## ADR 029-03: Ausencia de Datos Médicos Clínicos
- **Decisión**: Solo se registra la aptitud física/mental como metadata (`FIT`, `UNFIT`, `PENDING`) con vigencia y emisor.
- **Estado**: Aprobado.
