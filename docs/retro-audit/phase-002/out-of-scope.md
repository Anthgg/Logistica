# Exclusiones de Alcance · Fase 002

Este documento establece formalmente los límites del sistema para el **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales**, diferenciando con total claridad las exclusiones oficiales confirmadas por el Plan Maestro de aquellas propuestas derivadas del análisis técnico que se encuentran pendientes de decisión por el usuario.

---

## 1. Exclusiones Oficiales del Primer Lanzamiento (OFFICIAL_OUT_OF_SCOPE_V1)

### 1.1. Facturación Tributaria Automática (AUTOMATIC_TAX_BILLING)
- **Clasificación:** `OFFICIAL_OUT_OF_SCOPE_V1`
- **Estado de Decisión:** `CONFIRMED_BY_MASTER_PLAN`
- **Definición:** Emisión directa, validación contable y timbrado fiscal automático de comprobantes de pago tributarios (Facturas electrónicas, Boletas de venta electrónicas, Notas de crédito/débito fiscales ante la SUNAT u homólogos de administración tributaria).
- **Justificación Oficial:** El sistema T1 es un **Sistema de Gestión Logística, Almacenes y Trazabilidad Operativa (WMS/TMS)**. Las obligaciones fiscales y contables de facturación tributaria corresponden exclusivamente a los sistemas ERP contables, de facturación electrónica o plataformas OSE autorizadas de la organización.
- **Frontera de Interfaz:**
  - El sistema **SÍ** genera documentos de traslado logístico (como la Guía de Remisión Electrónica - GRE y Actas de Entrega/Recepción).
  - El sistema **SÍ** registra referencias documentales (número de factura de compra del proveedor, número de comprobante de compra) como campos de metadatos informativos para conciliación física.
  - El sistema **NO** emite facturas tributarias de venta ni se comunica con APIs fiscales para declarar impuestos o calcular balances contables impositivos.

---

## 2. Exclusiones Propuestas Pendientes de Decisión (PROPOSED_OUT_OF_SCOPE_V1)

Las siguientes exclusiones corresponden a recomendaciones técnicas y de frontera funcional formuladas durante la retro-auditoría. No constituyen decisiones aprobadas del proyecto hasta que sean validadas formalmente por el usuario.

### 2.1. Procesamiento de Pasarelas de Pago Bancario (PAYMENT_GATEWAY_PROCESSING)
- **Clasificación:** `PROPOSED_OUT_OF_SCOPE_V1`
- **Estado de Decisión:** `PENDING_USER_SCOPE_DECISION`
- **Descripción:** Procesamiento de cobros monetarios directos mediante tarjetas de crédito, débito, transferencias bancarias en línea o pasarelas de pago externas (Stripe, PayPal, Niubiz, etc.).
- **Racional Propuesto:** Las liquidaciones comerciales y cobranzas suelen gestionarse en el sistema de ventas/ERP comercial externo.

### 2.2. Contabilidad General y Libros Contables Tributarios (FINANCIAL_ACCOUNTING)
- **Clasificación:** `PROPOSED_OUT_OF_SCOPE_V1`
- **Estado de Decisión:** `PENDING_USER_SCOPE_DECISION`
- **Descripción:** Mantenimiento de Libro Mayor, Libro Diario y generación de balances financieros de pérdidas y ganancias.
- **Racional Propuesto:** El libro de inventario (`inventory_ledger`) opera estrictamente a nivel de **unidades físicas y movimientos de existencias**, delegando la contabilidad financiera al sistema corporativo.

### 2.3. Planillas y Recursos Humanos (PAYROLL_AND_HR)
- **Clasificación:** `PROPOSED_OUT_OF_SCOPE_V1`
- **Estado de Decisión:** `PENDING_USER_SCOPE_DECISION`
- **Descripción:** Cálculo de remuneraciones, horas extras, beneficios sociales y procesamiento de nómina de personal.
- **Racional Propuesto:** La gestión de conductores y almacenistas en T1 se restringe a sus atributos operativos, permisos y turnos de asignación en rutas/muelles.

### 2.4. Mantenimiento Mecánico Mayor de Vehículos (FLEET_HEAVY_MAINTENANCE)
- **Clasificación:** `PROPOSED_OUT_OF_SCOPE_V1`
- **Estado de Decisión:** `PENDING_USER_SCOPE_DECISION`
- **Descripción:** Gestión de talleres mecánicos, compras de repuestos automotrices y mantenimiento correctivo mayor de motores pesados.
- **Racional Propuesto:** El sistema T1 controla el estado legal y documental de la flota (SOAT, revisiones técnicas vigentes, inspecciones de garita), delegando reparaciones mecánicas a software de taller especializado.

---

## 3. Exclusiones Rechazadas (REJECTED_PROPOSALS)
*(Ninguna propuesta rechazada actualmente)*

---

## 4. Cuadro Resumen de Clasificación de Exclusiones

| Capacidad / Módulo | Clasificación | Estado de Decisión |
| :--- | :--- | :--- |
| **Facturación Tributaria Automática (`AUTOMATIC_TAX_BILLING`)** | `OFFICIAL_OUT_OF_SCOPE_V1` | `CONFIRMED_BY_MASTER_PLAN` |
| **Pasarelas de Pago (`PAYMENT_GATEWAY_PROCESSING`)** | `PROPOSED_OUT_OF_SCOPE_V1` | `PENDING_USER_SCOPE_DECISION` |
| **Contabilidad General Financiera (`FINANCIAL_ACCOUNTING`)** | `PROPOSED_OUT_OF_SCOPE_V1` | `PENDING_USER_SCOPE_DECISION` |
| **Planillas y Recursos Humanos (`PAYROLL_AND_HR`)** | `PROPOSED_OUT_OF_SCOPE_V1` | `PENDING_USER_SCOPE_DECISION` |
| **Mantenimiento Mecánico Pesado (`FLEET_HEAVY_MAINTENANCE`)** | `PROPOSED_OUT_OF_SCOPE_V1` | `PENDING_USER_SCOPE_DECISION` |
