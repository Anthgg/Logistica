# Registro de Decisiones de Arquitectura (ADR) y Temas Diferidos

## ADR 027-01: Uso de Tipos `Decimal` para Masa y Volumen

* **Estado**: APROBADO
* **Contexto**: La representación de pesos vehiculares en flotantes (`float`) generaba inconsistencias marginales de redondeo ($20.000000000000004\text{ kg}$) al calcular capacidades de carga útil en despachos pesados.
* **Decisión**: Utilizar `Numeric(12,4)` en PostgreSQL mapeado a `Decimal` en Python/SQLAlchemy para todas las métricas de peso, masa y volumen.
* **Consecuencia**: Exactitud matemática garantizada en auditorías de balanza sin margen de error por coma flotante.

---

## ADR 027-02: Separación de Documentos y Matriz de Requisitos Dinámica

* **Estado**: APROBADO
* **Contexto**: Diferentes tipos de vehículos (ej: furgón urbano vs cisternas sustancias peligrosas) poseen distintas obligaciones legales ante el MTC y SUTRAN.
* **Decisión**: Crear la tabla `logistics_vehicle_document_requirements` para parametrizar de forma dinámica la obligatoriedad y los criterios de inhabilitación por vencimiento sin hardcodear reglas en código.

---

## ADR 027-03: Versionado por Snapshots SHA-256 Inmutables

* **Estado**: APROBADO
* **Contexto**: Ante siniestros en ruta o inspecciones del MTC/SUTRAN, es imperativo demostrar exactamente qué estado, póliza SOAT y placa tenía el vehículo en una fecha histórica previa.
* **Decisión**: Implementar `VehicleVersionModel` alimentado por `VehicleSnapshotProvider`, creando firmas SHA-256 inmutables de cada estado estructural.

---

## Temas Diferidos a Futuras Fases

1. **Integración con Servicios Web de SUNARP (Fase 028)**: Consulta automatizada de vigencia de Tarjeta de Propiedad y gravámenes vehiculares.
2. **Integración con Servicio Web de APESEG (Fase 028)**: Validación en tiempo real del número de consulta SOAT vía scraping/API oficial.
3. **Módulo de Mantenimiento Preventivo / Odómetro (Fase 040)**: Seguimiento de lecturas de horómetro y kilometraje para alertas de cambio de aceite y neumáticos.
