# Exclusiones Oficiales del Primer Lanzamiento (OUT_OF_SCOPE_V1) · Fase 002

Este documento establece formalmente los límites del sistema, delimitando las capacidades que **NO forman parte del alcance del primer lanzamiento (V1)** del **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales**.

---

## 1. Exclusión Obligatoria Principal

### 1.1. Facturación Tributaria Automática (AUTOMATIC_TAX_BILLING)
- **Definición:** Emisión directa, validación contable y timbrado fiscal automático de comprobantes de pago tributarios (Facturas electrónicas, Boletas de venta electrónicas, Notas de crédito/débito fiscales ante la SUNAT u homólogos de administración tributaria).
- **Justificación de Exclusión:** El sistema T1 es un **Sistema de Gestión Logística, Almacenes y Trazabilidad Operativa (WMS/TMS)**. Las obligaciones fiscales y contables de facturación tributaria corresponden exclusivamente a los sistemas ERP contables, de facturación electrónica o plataformas OSE autorizadas de la organización.
- **Frontera de Interfaz:**
  - El sistema **SÍ** genera documentos de traslado logístico (como la Guía de Remisión Electrónica - GRE y Actas de Entrega/Recepción).
  - El sistema **SÍ** registra referencias documentales (número de factura de compra del proveedor, número de comprobante de compra) como campos de metadatos informativos para conciliación física.
  - El sistema **NO** emite facturas tributarias de venta ni se comunica con APIs fiscales para declarar impuestos o calcular balances contables impositivos.

---

## 2. Otras Exclusiones Formales del Primer Lanzamiento

### 2.1. Procesamiento de Pasarelas de Pago Bancario (PAYMENT_GATEWAY_PROCESSING)
- El sistema no procesa cobros monetarios directos mediante tarjetas de crédito, débito, transferencias bancarias en línea ni pasarelas de pago externas (tipo Stripe, PayPal, Niubiz, etc.).
- Las liquidaciones comerciales y cobranzas son gestionadas en el sistema de ventas/ERP comercial externo.

### 2.2. Contabilidad General y Libros Contables Tributarios (FINANCIAL_ACCOUNTING)
- El sistema no mantiene el Libro Mayor, Libro Diario ni genera balances financieros de pérdidas y ganancias.
- El libro de inventario (`inventory_ledger`) opera estrictamente a nivel de **unidades físicas y movimientos de existencias**, sin valorizaciones tributarias según normas contables NIIF/NIC.

### 2.3. Planillas y Recursos Humanos (PAYROLL_AND_HR)
- La gestión de conductores, almacenistas y supervisores se limita a sus roles operativos, permisos, licencias de conducir y turnos de asignación en muelles/rutas.
- No se incluye cálculo de remuneraciones, horas extras ni pagos de nómina.

### 2.4. Mantenimiento Mecánico Mayor de Vehículos (FLEET_HEAVY_MAINTENANCE)
- El sistema verifica el estado documental y legal de la flota (SOAT, revisiones técnicas vigentes, inspecciones de garita).
- No incluye el control de inventario de repuestos mecánicos, órdenes de taller ni mantenimiento predictivo de motores pesados.

---

## 3. Resumen de Fronteras de Alcance

| Capacidad | Clasificación | Manejo en el Sistema T1 |
| :--- | :--- | :--- |
| **Facturación de Venta Tributaria (SUNAT)** | `OUT_OF_SCOPE` | Delegado al ERP contable |
| **Guía de Remisión de Transporte (GRE)** | `IN_SCOPE` | Generado por el motor documental |
| **Comprobantes de Control de Garita** | `IN_SCOPE` | Generado con firma y evidencias |
| **Pasarelas de Pago** | `OUT_OF_SCOPE` | Sin integración en V1 |
| **Libro de Existencias Físicas (Kárdex Operativo)** | `IN_SCOPE` | Registrado en Inventory Ledger |
| **Libros Contables Tributarios Oficiales** | `OUT_OF_SCOPE` | Delegado a Finanzas/Contabilidad |
