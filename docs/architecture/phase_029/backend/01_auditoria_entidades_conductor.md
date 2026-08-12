# 01 — Auditoría de Entidades de Conductor Previs y Justificación de Arquitectura

## Auditoría de Entidades Existentes

Previo a la concepción de la **Fase 029 (Maestro de Conductores)**, se realizó una auditoría exhaustiva en la base de código backend (`backend/app/models/`, `backend/app/schemas/`, scripts de migración DDL anteriores).

### Hallazgos de la Auditoría:
1. **Ausencia de Modelo ORM de Conductor**: No existía ningún modelo SQLAlchemy ni tabla PostgreSQL que representara la entidad `Driver` en el sistema.
2. **Entidades Relacionadas Existentes**:
   - `User` (`app.models.user.User`): Cuenta de usuario para autenticación y RBAC general del sistema.
   - `Employee` (`app.models.hr.Employee`): Ficha de personal de recursos humanos (nómina, asistencia, contrato).
   - `BusinessPartner` (`app.models.logistics.BusinessPartner`): Tercero comercial (proveedor, cliente, transportista).
   - `VehicleModel` (`logistics_vehicles` - Fase 027): Maestro de vehículos.
   - `VehicleVerificationModel` (`logistics_vehicle_verifications` - Fase 028): Verificaciones de placas.

3. **Inconveniente de Diseños Monolíticos Previos en la Industria**:
   En muchos sistemas legacy, se solía sobrecargar la tabla `users` o `employees` agregando columnas como `license_number` o `is_driver`. Esto genera acoplamiento severo, impide gestionar conductores de empresas transportistas subcontratadas (que no son ni empleados ni usuarios del sistema) y vulnera normativas de protección de datos personales y privacidad.

---

## Justificación de la Arquitectura Limpia de 16 Tablas

Para abordar los requisitos normativos del MTC (Ministerio de Transportes y Comunicaciones de Perú), normativas de seguridad en el transporte de materiales peligrosos (Hazmat), normativas de salud ocupacional y privacidad (LPDP Ley 29733 / GDPR), la Fase 029 adopta una **Arquitectura Limpia y Desacoplada basada en 16 Tablas Relacionales**.

### Principios Fundamentales del Diseño:

1. **Desacoplamiento Estricto de Dominio**:
   Un `Driver` representa un **rol operativo en el dominio de transportes y logística**. Un conductor puede ser:
   - Un empleado propio (vinculado opcionalmente a `Employee`).
   - Un usuario del sistema móvil/web (vinculado opcionalmente a `User`).
   - Un chofer externo contratado por una empresa transportista socio de negocio (vinculado a `BusinessPartner` con rol `CARRIER`).
   - Un chofer independiente o multitransportista.

2. **Normalización vs Auditabilidad**:
   - **Documentos de Identidad (`logistics_driver_identity_documents`)**: Separados para soportar múltiples documentos por persona (DNI, Carnet de Extranjería, Pasaporte) con atributos de verificación, fecha de emisión/expiración y enmascaramiento.
   - **Licencias de Conducir (`logistics_driver_licenses`)**: Separadas del conductor para soportar recategorizaciones, renovaciones, suspensiones históricas e historial de puntos.
   - **Categorías y Restricciones M:N**: Las categorías de licencia MTC (A-I a A-IIIc) y sus restricciones (lentes, audífonos, transmisión automática) se modelan mediante tablas intermedias para permitir consultas precisas de compatibilidad con vehículos.

3. **Seguridad y Privacidad por Diseño (Privacy by Design)**:
   - **Fotografías (`logistics_driver_photos`)**: Almacenamiento exclusivamente mediante referencias opacas `file_reference_id` hacia el Object Storage (S3/MinIO). Prohibición explícita de campos Base64 en BD y prohibición de almacenar plantillas biométricas faciales en el maestro.
   - **Documentos Médicos/Capacitaciones (`logistics_driver_documents`)**: Se guarda la aptitud médica como booleano/estado (`FIT`, `UNFIT`, `FIT_WITH_RESTRICTIONS`) y fecha de vencimiento, respetando la confidencialidad de la historia clínica.

4. **Inmutabilidad y Concurrencia Optimista**:
   - Cada cambio de estado genera un snapshot JSONB con hash SHA-256 en `logistics_driver_versions`.
   - Modificaciones concurrentes protegidas por el campo `row_version` (incremento entero).

---

## Estructura Relacional Sintetizada

```
logistics_drivers (Entidad Raíz)
 ├── logistics_driver_identity_documents (1:N)
 ├── logistics_driver_licenses (1:N)
 │    ├── logistics_driver_license_category_assignments (M:N) --> logistics_driver_license_categories
 │    └── logistics_driver_license_restrictions (1:N)
 ├── logistics_driver_carrier_assignments (1:N) --> BusinessPartner (CARRIER)
 ├── logistics_driver_contacts (1:N)
 ├── logistics_driver_emergency_contacts (1:N)
 ├── logistics_driver_photos (1:N)
 ├── logistics_driver_documents (1:N)
 ├── logistics_driver_operational_restrictions (1:N)
 ├── logistics_driver_versions (1:N)
 └── logistics_driver_user_account_links (1:1 opcional) --> User
```

Esta separación garantiza cero redundancia, máxima flexibilidad operativa y cumplimiento normativo estricto.
