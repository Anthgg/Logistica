# Inclusiones del Primer Lanzamiento (IN_SCOPE_V1) · Fase 002

Este documento detalla las funcionalidades y capacidades incluidas oficialmente en el alcance del producto para el **Proyecto T1: Sistema Logístico, Trazabilidad y Rutas Reales**.

---

## 1. Categorías Funcionales Incluidas

### 1.1. Compras y Aprovisionamiento (Purchasing / Procurement)
- Gestión de requerimientos de compra internos y solicitudes de cotización.
- Evaluación y homologación de proveedores.
- Emisión, cálculo de costos y montos, y ciclo de vida de órdenes de compra (OC).
- Flujo de aprobaciones jerárquicas con validación reforzada (Step-Up authentication).

### 1.2. Recepción e Ingreso (Receiving / Inbound)
- Avisos de llegada de mercancía y programación de citas/calendario de recepción.
- Control de garita/puerta (registro de placa, conductor, empresa de transporte, peso y precintos).
- Asignación de muelles de descarga y control de tiempos de operación.
- Recepción física por escaneo y conteo de bultos.
- Registro y liquidación de diferencias de recepción (faltantes, sobrantes, mermas).
- Planes de inspección de calidad en recepción y gestión de cuarentena/liberación.

### 1.3. Almacenes y Zonificación (Warehousing)
- Modelado jerárquico de almacenes (sedes, almacenes principales/secundarios).
- Zonificación física y lógica (zonas de recepción, cuarentena, almacenamiento general, picking, staging, despacho).
- Estructuración de ubicaciones, pasillos, racks, niveles y compartimentos (bins).
- Estrategias de ubicación dirigida (Putaway dirigido por reglas).

### 1.4. Inventario y Saldos (Inventory)
- Libro inmutable de movimientos de inventario (Inventory Ledger - partida doble logística).
- Cálculo en tiempo real de saldos disponibles, reservados, en cuarentena y bloqueados.
- Ajustes de inventario justificados y autorizados.
- Conteos físicos y toma de inventario cíclico.
- Transferencias y traslados entre almacenes de la organización.

### 1.5. Trazabilidad y Auditoría (Traceability)
- Registro inmutable de eventos de auditoría (quién, qué, cuándo, desde qué IP/dispositivo).
- Identificación de lotes y fechas de vencimiento en recepciones e inventario.
- Trazabilidad documental de punta a punta (Requerimiento -> OC -> Guía/Recepción -> Movimiento de Stock -> Despacho -> Entrega).

### 1.6. Salida y Despacho (Outbound)
- Pedidos de salida y asignación de prioridades.
- Reserva preventiva de stock para órdenes confirmadas.
- Flujos de preparación de pedidos: picking por listas/olas y packing/consolidación de bultos.
- Planificación y consolidación de cargas para despacho.
- Emisión de órdenes de salida y autorización de despacho con Step-Up biológico/multimodal.

### 1.7. Transporte y Gestión de Flota (Transport)
- Maestro de vehículos propios y de terceros (placas, marcas, capacidades de carga, configuración de ejes, SOAT, revisiones técnicas).
- Maestro de conductores (licencias de conducir, vigencia, categorización).
- Verificación automática de estado de placas y licencias ante entidades regulatorias.
- Planificación y trazado de rutas de transporte.

### 1.8. Entrega y Prueba de Recepción (Delivery)
- Asignación de despachos a rutas y conductores.
- Registro de Prueba de Entrega (Proof of Delivery - POD): firma digital, geolocalización, fotografía de evidencia y datos del receptor.
- Gestión de entregas parciales y motivos de rechazo en punto de destino.

### 1.9. Devoluciones y Logística Inversa (Returns)
- Registro y gestión de incidencias logísticas en ruta o recepción.
- Solicitudes de devolución autorizadas (RMA).
- Inspección técnica de mercancía devuelta y reclasificación de destino (reingreso a stock, reacondicionamiento o merma/baja).

### 1.10. Motor Documental y Evidencias (Documents Engine)
- Catálogo centralizado de tipos documentales institucionales y logísticos.
- Gestión de series y talonarios con numeración correlativa segura y anti-colisión.
- Motor de plantillas HTML/CSS con inyección dinámica y renderizado PDF de alta fidelidad.
- Generación de documentos logísticos clave: Guías de Remisión Electrónica (GRE), Comprobantes de Garita, Actas de Diferencias, Hojas de Ruta, Etiquetas de Identificación.
- Repositorio central de archivos y evidencias con hashing criptográfico SHA-256 e inspección de seguridad (antivirus/XXE).

### 1.11. KPIs y Analítica Operativa (Analytics)
- Tableros de control interactivos en tiempo real para supervisores y administradores.
- Métricas de eficiencia de compras, rotación de inventario, tiempos de descarga en muelles y cumplimiento de entregas (OTIF - On-Time In-Full).
- Exportación de reportes operativos en formatos estandarizados.

### 1.12. Integraciones Externas de Soporte (Integrations)
- Consulta y validación de RUC y razón social (SUNAT API / Web Scraping con fallback).
- Verificación de placas vehiculares y licencias de conducir.
- Servicios de geocodificación y renderizado de mapas (MapLibre / OSRM).
