# Registro de Decisiones de Arquitectura (ADR 028-01 a ADR 028-05)

## 1. Resumen de Decisiones de Arquitectura

El presente documento registra las **Decisiones de Arquitectura (Architectural Decision Records - ADR)** que rigen el diseño, límites normativos y patrones de diseño del subsistema de verificaciones vehiculares (Fase 028).

---

## 2. ADR 028-01: Prohibición Absoluta de Scraping Web y Bypass CAPTCHA (`ZERO SCRAPING`)

* **Estado**: `APROBADO`
* **Fecha**: 2026-07-28
* **Contexto**: Diversas iniciativas plantean consultar directamente los portales públicos web de SUNARP, MTC o SAT parseando HTML o automatizando navegadores headless para evitar costos de API.
* **Decisión**: Se prohíbe de forma absoluta e incondicional cualquier técnica de scraping web, elusión de CAPTCHA o uso de peticiones no documentadas contra portales gubernamentales. Toda integración debe ser efectuada mediante APIs oficiales B2B o canalizada a través del flujo de **Verificación Asistida por Operador**.
* **Consecuencias**:
  * *Positivas*: Cumplimiento estricto de la Ley N° 30096 (Delitos Informáticos), SLA garantizado sin bloqueos de IP ni roturas de HTML.
  * *Negativas*: Los datos de entidades sin API abierto deberán ingresarse manualmente mediante verificación asistida.

---

## 3. ADR 028-02: Adopción del Patrón Adapter / Strategy con Proveedores Fake Deterministas

* **Estado**: `APROBADO`
* **Fecha**: 2026-07-28
* **Contexto**: Las pruebas automatizadas y entornos locales de desarrollo no deben depender de la disponibilidad, cuotas ni conectividad con servicios HTTP externos.
* **Decisión**: Toda comunicación con proveedores de verificación debe encapsularse tras la interfaz abstracta `VehicleVerificationProvider`, suministrando las implementaciones `FakeVehicleVerificationProvider` y `NoOpVehicleVerificationProvider` para pruebas deterministas.
* **Consecuencias**:
  * *Positivas*: Ejecución de suites de prueba en < 1 segundo sin llamadas HTTP de red, 100% de aislamiento.
  * *Negativas*: Mantenimiento del diccionario mock de pruebas para reflejar nuevos escenarios edge-case.

---

## 4. ADR 028-03: Segregación Estricta de Funciones (`Four-Eyes Principle`) en Verificaciones Asistidas

* **Estado**: `APROBADO`
* **Fecha**: 2026-07-28
* **Contexto**: El ingreso manual de verificaciones asistidas presenta riesgos de fraude o registro de datos complacientes si un solo usuario controla el flujo completo.
* **Decisión**: Se implementa la regla estricta `created_by != approved_by` en el servicio y mediante una restricción `CHECK` a nivel de base de datos en `logistics_assisted_vehicle_verifications`. Ningún usuario puede auto-aprobar las verificaciones que haya registrado.
* **Consecuencias**:
  * *Positivas*: Eliminación del riesgo de autocontrol y cumplimiento de estándares de auditoría ISO 27001 / SOC2.
  * *Negativas*: Requiere la intervención de al menos dos roles distintos (Operador y Supervisor) para validar verificaciones manuales.

---

## 5. ADR 028-04: Firma Criptográfica SHA-256 y Provenance a Nivel de Campo (`Field Provenance`)

* **Estado**: `APROBADO`
* **Fecha**: 2026-07-28
* **Contexto**: Es necesario garantizar que los payloads devueltos por fuentes externas no puedan ser alterados maliciosamente en la base de datos y que cada campo verificado tenga trazabilidad directa a su origen.
* **Decisión**: El `raw_payload` entregado por la fuente se firma inmediatamente con un hash **SHA-256** canonicalizado en `VehicleVerificationResultModel`, y se desgloza cada atributo individual en `VehicleVerificationFieldProvenanceModel`.
* **Consecuencias**:
  * *Positivas*: Inmutabilidad auditable no repudiable ante arbitrajes o litigios.
  * *Negativas*: Ligero incremento en el espacio en disco por el almacenamiento estructurado de provenance por campo.

---

## 6. ADR 028-05: Aplicación Controlada con Congelamiento de Snapshots Inmutables

* **Estado**: `APROBADO`
* **Fecha**: 2026-07-28
* **Contexto**: Al actualizar el Maestro de Vehículos (`VehicleModel`) con datos verificados, se debe preservar la historia completa del estado que tenía el vehículo en versiones anteriores.
* **Decisión**: `ApplyVehicleVerificationService` actualiza los atributos del vehículo y genera de forma atómica un nuevo snapshot en `VehicleVersionModel` (entidad de la Fase 027), firmándolo criptográficamente con SHA-256.
* **Consecuencias**:
  * *Positivas*: Trazabilidad histórica completa del ciclo de vida del vehículo sin perdida de estados pasados.
  * *Negativas*: Operación de aplicación requiere permisos Step-Up Authentication y escritura en dos agregados relacionales.
