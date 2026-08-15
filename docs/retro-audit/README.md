# Matriz Maestra de Retro-Auditoría · Proyecto T1 Logística

Este documento contiene el registro de estado maestro de las 100 fases del **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales** (Plan Maestro de Implementación en 100 Fases, Versión 1.0, 26 de julio de 2026). Cada fase debe ser rigurosamente auditada, probada, documentada y validada mediante prueba de aceptación de usuario (UAT) antes de autorizar el inicio de la siguiente fase.

> **Regla de Ejecución:** Ninguna fase puede iniciarse hasta que la fase inmediatamente anterior tenga estado PASSED y cuente con aprobación formal de usuario y merge validado en CI.

---

## 1. Resumen Ejecutivo de Estado

- **Fase en Curso:** F001 — Congelar la línea base del proyecto
- **Estado de la Fase F001:** READY_FOR_UAT
- **Estado de Aceptación de Usuario (F001):** PENDING_USER_TEST
- **Fase F002:** BLOCKED (No autorizada hasta que F001 sea completada, aceptada por el usuario y mergeada)
- **Fases F003 a F100:** BLOCKED

---

## 2. Tabla Maestra de Fases (F001 - F100)

| Fase | Título oficial | Bloque | Estado | README | UAT |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F001** | Congelar la línea base del proyecto | Base e integración | PASSED | YES | PASS |
| **F002** | Definir el alcance logístico | Base e integración | IN_PROGRESS | YES | PENDING_USER_REVIEW |
| **F003** | Diseñar la arquitectura modular | Base e integración | BLOCKED | NO | NOT_STARTED |
| **F004** | Definir organización, sedes y almacenes | Base e integración | BLOCKED | NO | NOT_STARTED |
| **F005** | Definir roles logísticos | Base e integración | BLOCKED | NO | NOT_STARTED |
| **F006** | Definir permisos por acción | Base e integración | BLOCKED | NO | NOT_STARTED |
| **F007** | Unificar eventos de auditoría | Base e integración | BLOCKED | NO | NOT_STARTED |
| **F008** | Integrar la autenticación existente | Base e integración | BLOCKED | NO | NOT_STARTED |
| **F009** | Integrar autenticación continua | Base e integración | BLOCKED | NO | NOT_STARTED |
| **F010** | Preparar ambientes y despliegue | Base e integración | BLOCKED | NO | NOT_STARTED |
| **F011** | Crear el catálogo de documentos | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F012** | Definir el estándar de códigos | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F013** | Diseñar series y talonarios | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F014** | Crear el motor de plantillas | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F015** | Diseñar documentos de compras | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F016** | Diseñar documentos de ingreso | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F017** | Diseñar documentos de inventario | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F018** | Diseñar documentos de salida | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F019** | Diseñar documentos de transporte y entrega | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F020** | Implementar descarga, reimpresión y anulación | Motor documental | BLOCKED | NO | NOT_STARTED |
| **F021** | Configurar datos de la empresa | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F022** | Modelar almacenes y ubicaciones | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F023** | Crear el catálogo de productos | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F024** | Implementar unidades y conversiones | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F025** | Crear socios de negocio | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F026** | Integrar consulta de RUC | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F027** | Crear el maestro de vehículos | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F028** | Implementar verificaciones de placa | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F029** | Crear el maestro de conductores | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F030** | Centralizar archivos y evidencias | Maestros e integraciones | BLOCKED | NO | NOT_STARTED |
| **F031** | Implementar requerimientos de compra | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F032** | Implementar solicitudes de cotización | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F033** | Implementar evaluación de proveedores | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F034** | Implementar órdenes de compra | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F035** | Implementar aprobaciones de compras | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F036** | Implementar aviso de llegada | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F037** | Implementar control de puerta | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F038** | Implementar asignación de muelle y descarga | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F039** | Implementar recepción por escaneo | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F040** | Implementar diferencias de recepción | Compras e ingreso | BLOCKED | NO | NOT_STARTED |
| **F041** | Configurar planes de calidad | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F042** | Implementar cuarentena y liberación | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F043** | Implementar ubicación dirigida | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F044** | Crear el libro de inventario | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F045** | Calcular saldos de stock | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F046** | Implementar lotes, series y unidades logísticas | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F047** | Implementar ajustes de inventario | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F048** | Implementar conteos físicos | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F049** | Implementar transferencias entre almacenes | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F050** | Cerrar recepción de transferencias | Calidad e inventario | BLOCKED | NO | NOT_STARTED |
| **F051** | Implementar pedidos de salida | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F052** | Implementar reserva de stock | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F053** | Implementar picking | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F054** | Implementar packing | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F055** | Planificar el despacho | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F056** | Emitir la orden de salida | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F057** | Liberar el despacho con step-up | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F058** | Controlar carga y precinto | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F059** | Generar el paquete de despacho | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F060** | Gestionar reimpresión y cancelación de salida | Salida y despacho | BLOCKED | NO | NOT_STARTED |
| **F061** | Seleccionar la estrategia de mapas | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F062** | Integrar MapLibre en React | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F063** | Implementar geocodificación | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F064** | Modelar planes de ruta | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F065** | Consumir un motor de direcciones real | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F066** | Ingerir GPS del conductor | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F067** | Mostrar vehículos en tiempo real | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F068** | Implementar map matching y desvíos | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F069** | Crear geocercas y checkpoints | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F070** | Implementar modo offline y contingencia | Rutas y mapas reales | BLOCKED | NO | NOT_STARTED |
| **F071** | Crear la experiencia del conductor | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F072** | Implementar prueba de entrega | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F073** | Gestionar entrega parcial o rechazada | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F074** | Validar evidencia de entrega | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F075** | Implementar autorización de devolución | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F076** | Planificar recojo inverso | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F077** | Inspeccionar devolución | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F078** | Implementar incidencias logísticas | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F079** | Gestionar reclamos y acciones correctivas | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F080** | Configurar notificaciones y escalamiento | Entrega y logística inversa | BLOCKED | NO | NOT_STARTED |
| **F081** | Diseñar la capa de KPIs | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F082** | Implementar KPIs de compras | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F083** | Implementar KPIs de recepción | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F084** | Implementar KPIs de inventario | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F085** | Implementar KPIs de preparación | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F086** | Implementar KPIs de transporte y entrega | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F087** | Implementar KPIs documentales | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F088** | Construir dashboards React | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F089** | Implementar exportaciones gerenciales | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F090** | Preparar analítica y modelos futuros | KPIs y analítica | BLOCKED | NO | NOT_STARTED |
| **F091** | Endurecer seguridad de APIs | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F092** | Aplicar privacidad y minimización | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F093** | Asegurar integridad documental | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F094** | Crear pruebas unitarias y de contrato | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F095** | Crear pruebas end-to-end | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F096** | Ejecutar pruebas de carga y resiliencia | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F097** | Realizar aceptación con usuarios | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F098** | Migrar maestros y saldos iniciales | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F099** | Ejecutar piloto controlado | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |
| **F100** | Desplegar y gobernar producción | Seguridad, pruebas y producción | BLOCKED | NO | NOT_STARTED |

---

## 3. Criterios de Aceptación para Desbloquear Fases Subsiguientes

1. **Auditoría Técnica Completa:** Inspección de endpoints, esquemas DB, Alembic, contratos protegidos y seguridad.
2. **Correcciones de Defectos F001:** Sin introducir refactorizaciones fuera de alcance o dependencias innecesarias.
3. **Tests 100% Verdes:** Backend (unit, security, e2e) y Frontend (typecheck, lint, vitest, build).
4. **Documentación Completa:** 28 secciones mandatorias de auditoría archivadas en docs/retro-audit/phase-XXX/README.md.
5. **Prueba de Aceptación de Usuario (UAT):** Verificación manual funcional ejecutada por el usuario.
6. **Merge Limpio y CI Post-Merge:** Fusión a main y confirmación de build limpio en el commit exacto.
