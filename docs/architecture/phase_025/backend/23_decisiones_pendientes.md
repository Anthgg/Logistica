# 23. Registro de Decisiones de Arquitectura (ADRs)

## Registro de Decisiones TÉcnicas de la Fase 025

---

### ADR 025-01: Adopción del Modelo Unificado `BusinessPartner` frente a Entidades Segregadas

* **Estado:** ACEPTADO
* **Fecha:** 2026-07-28
* **Contexto:** Se requería definir si los proveedores, clientes y transportistas debían residir en tablas físicas separadas (`suppliers`, `customers`, `carriers`) o unificarse bajo una sola entidad maestra Party/BusinessPartner.
* **Decisión:** Implementar el modelo maestro único `BusinessPartnerModel` respaldado por la tabla `business_partners` y perfiles 1:1 condicionales por rol (`business_partner_roles`).
* **Consecuencias:** Elimina la duplicación de identificadores fiscales (RUC/DNI), garantiza la consistencia en facturación electrónica y permite una vista 360 del historial comercial del socio.

---

### ADR 025-02: Generación Determinística de Códigos Correlativos con Secuencia Atómica

* **Estado:** ACEPTADO
* **Fecha:** 2026-07-28
* **Contexto:** El sistema requiere un identificador de negocio amigable (`partner_code`) en formato `BP-XXXXXX` único por organización y resistente a race conditions bajo concurrencia.
* **Decisión:** Implementar la tabla de secuencia aislada `business_partner_sequences` con bloqueo pesimista `SELECT ... FOR UPDATE` en `BusinessPartnerCodeService`.
* **Consecuencias:** Se elimina completamente el riesgo de códigos duplicados o race conditions bajo requests simultáneos. Se impone inmutabilidad estricta tras el primer INSERT.

---

### ADR 025-03: Deslinde de Validación Sintáctica de RUC respecto a Consultas SUNAT en Tiempo Real

* **Estado:** ACEPTADO
* **Fecha:** 2026-07-28
* **Contexto:** La validación de RUCs en Perú puede ejecutarse de forma matemática offline (Módulo 11) o mediante scraping/API en tiempo real contra padrones de la SUNAT.
* **Decisión:** Acotar el alcance de la Fase 025 exclusivamente a la validación sintáctica matemática Módulo 11 mediante `PeruvianRucValidator`. Las consultas web a la SUNAT/RENIEC se desacoplaron contractualmente hacia la Fase 026.
* **Consecuencias:** Cero latencia o caídas en la creación de socios cuando los servidores de la SUNAT experimentan degradación.

---

### ADR 025-04: Independencia Estricta de Estados Operativos por Rol

* **Estado:** ACEPTADO
* **Fecha:** 2026-07-28
* **Contexto:** Si un socio comete un incumplimiento de entregas como proveedor, debía evaluarse si dicha penalización debía inhabilitarlo automáticamente como cliente de ventas.
* **Decisión:** Garantizar aislamiento de estado a nivel de `BusinessPartnerRoleModel`. Suspender un rol (`SUPPLIER`) no afecta la operatividad de otros roles (`CUSTOMER`). La única excepción es el estado global de cabecera `BLOCKED`.
* **Consecuencias:** Máxima flexibilidad comercial sin sacrificar la seguridad financiera en caso de bloqueos graves de cumplimiento.

---

### ADR 025-05: Estrategia de Versionado Forense con Snapshots JSONB y Hash SHA-256

* **Estado:** ACEPTADO
* **Fecha:** 2026-07-28
* **Contexto:** Auditoría exigía trazabilidad no repudiable de los cambios en cuentas bancarias, razones sociales y direcciones fiscales de los socios.
* **Decisión:** Generar snapshots inmutables en JSONB ordenados determinísticamente en la tabla `business_partner_versions` con su correspondiente firma hash SHA-256 (`content_hash`) en cada mutación.
* **Consecuencias:** Permite reconstruir con precisión matemática la ficha del socio en cualquier instante del tiempo para peritajes legales o auditorías impositivas.
