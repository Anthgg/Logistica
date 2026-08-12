# 33 — Registro de Decisiones de Arquitectura (ADRs 026-01 a 026-05)

## ADR 026-01: Prohibición de Web Scraping y Adopción del Padrón Reducido SUNAT
- **Estado**: Aprobado.
- **Contexto**: Necesidad de consultar información de RUCs de forma masiva y confiable.
- **Decisión**: Se prohíbe el web scraping sobre la web interactiva de SUNAT por fragilidad y riesgo de IP blocking. Se adopta la ingesta masiva del Padrón Reducido oficial en formato ZIP.

## ADR 026-02: Esquema de Staging y Conmutación Atómica de Punteros
- **Estado**: Aprobado.
- **Contexto**: Evitar tiempo de inactividad (*downtime*) o consultas parciales durante la ingesta de 10 millones de filas.
- **Decisión**: Los registros se ingestan con estado `STAGED`. La conmutación a `ACTIVE` ocurre en una única transacción SQL atómica.

## ADR 026-03: No Sobrescritura Automática del Maestro de Socios Comerciales
- **Estado**: Aprobado.
- **Contexto**: Mantener la integridad de los datos declarados y contractuales en `business_partners`.
- **Decisión**: Los datos de SUNAT actualizan el perfil de verificación pero NUNCA modifican silenciosamente los campos del socio. Las discrepancias generan un `RucDataConflictModel`.

## ADR 026-04: Estrategia de Caché Tagged por `dataset_version_id`
- **Estado**: Aprobado.
- **Contexto**: Invalidador de caché eficiente tras la conmutación de un dataset sin recorrer claves Redis.
- **Decisión**: Se incluye el ID de versión en el prefijo de la clave de caché (`ruc:{dataset_version_id}:{normalized_ruc}`).

## ADR 026-05: Verificación Asistida Oficial bajo Regla de Cuatro Ojos
- **Estado**: Aprobado.
- **Contexto**: Proveer mecanismo para RUCs recién creados no presentes en el padrón mensual.
- **Decisión**: Permitir registro manual de verificación con evidencia previa aprobación obligatoria por un usuario distinto al creador.
