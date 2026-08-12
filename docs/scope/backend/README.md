# Fase 002 — Definición del Alcance Logístico del Backend (Proyecto T1)

## Índice de Documentación

1. [01_alcance_backend.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/01_alcance_backend.md): Inclusiones, exclusiones, restricciones y supuestos del backend.
2. [02_dominios_backend.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/02_dominios_backend.md): Los 32 dominios funcionales analizados y sus responsabilidades.
3. [03_modulos_propuestos.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/03_modulos_propuestos.md): Estructura de módulos bajo el prefijo `/api/logistics`.
4. [04_flujos_operativos.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/04_flujos_operativos.md): Flujos end-to-end con diagramas de secuencia/estados Mermaid.
5. [05_entidades_conceptuales.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/05_entidades_conceptuales.md): Catálogo conceptual de entidades del modelo de dominio.
6. [06_estados_negocio.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/06_estados_negocio.md): Máquinas de estado conceptuales y reglas de transición.
7. [07_actores_responsabilidades.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/07_actores_responsabilidades.md): Definición de actores, matriz de permisos y separación de funciones.
8. [08_seguridad_acciones_sensibles.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/08_seguridad_acciones_sensibles.md): Acciones sensibles, requerimientos de step-up y auditoría.
9. [09_integraciones_externas.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/09_integraciones_externas.md): Integraciones con SUNAT, SUNARP, MTC, Mapas, SMS y Almacenamiento.
10. [10_contratos_api_conceptuales.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/10_contratos_api_conceptuales.md): Contratos de recursos, verbos HTTP y parámetros conceptuales.
11. [11_matriz_mvp.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/11_matriz_mvp.md): Distribución por etapas (MVP 1, MVP 2, MVP 3, Consolidación).
12. [12_matriz_inclusion_exclusion.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/12_matriz_inclusion_exclusion.md): Matriz detallada de funcionalidades incluidas y excluidas.
13. [13_riesgos_backend.md](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/13_riesgos_backend.md): Riesgos técnicos, deuda técnica y decisiones pendientes.
14. [backend_scope_manifest.json](file:///c:/Users/anthg/OneDrive/Escritorio/proyecto%20tesis/autenticacion-continua/docs/scope/backend/backend_scope_manifest.json): Manifiesto estructurado JSON del alcance del backend.

## Objetivo de la Fase 002 Backend

Establecer la arquitectura funcional, el modelo de dominio conceptual, la división modular y los contratos API para la futura plataforma logística de **Proyecto T1**, garantizando la integración armónica con el backend FastAPI existente (autenticación continua, cookies HTTP-only, protección CSRF y despliegue en Google Cloud Run).

## Estado de la Línea Base (Fase 001)

- **Comprobación:** Se verificó la carpeta `docs/baseline/`.
- **Resultado:** Ausente. Se registra formalmente que los archivos de línea base (`01_inventario_tecnico.md` al `10_checklist_congelamiento.md`) no estaban presentes en el repositorio al inicio de esta fase. Toda la definición actual se fundamenta en la inspección directa del código fuente existente en `backend/app/`.

## Criterio de Ejecución

- **Modificaciones de Código:** Ninguna (0 líneas de código modificadas).
- **Base de datos / Migraciones:** Ninguna.
