# 02. Dominios Funcionales del Backend — Proyecto T1

Definición detallada de los 32 dominios funcionales analizados para el backend logístico:

| ID | Dominio | Objetivo Principal | Responsabilidad del Backend | Actores Clave | Prioridad / MVP |
|---|---|---|---|---|---|
| D01 | Configuración Organizacional | Definir la estructura de la entidad legal y parámetros globales. | Almacenar datos fiscales, zonas horarias, monedas y parámetros generales del sistema. | Administrador | MVP 1 |
| D02 | Sedes | Administrar las sedes físicas u operativas de la organización. | Mantenimiento de direcciones, ubigeos, contactos y vinculación con almacenes. | Administrador | MVP 1 |
| D03 | Almacenes | Gestionar instalaciones físicas de almacenamiento. | Clasificación de almacenes (Central, Transitario, Cuarentena), capacidad y asignación de personal. | Jede de Almacén | MVP 1 |
| D04 | Ubicaciones Internas | Definir la topología interna del almacén (Pasillos, Racks, Niveles, Cajas). | Estructura jerárquica de ubicaciones, control de capacidad volumétrica y peso máximo. | Almacenero | MVP 1 |
| D05 | Productos | Gestionar el catálogo de artículos/SKUs. | Control de SKUs, descripciones, categorías, atributos físicos (peso, volumen), flag de lote/serie. | Gestor de Catálogo | MVP 1 |
| D06 | Unidades de Medida | Definir unidades físicas y factores de conversión. | Mantenimiento de UOM (UND, KG, CJ, BL), conversiones estándar y conversiones específicas por SKU. | Gestor de Catálogo | MVP 1 |
| D07 | Proveedores | Registrar la base de datos de abastecedores. | Almacenamiento de RUC, Razón Social, condiciones de pago, evaluación de homologación y contactos. | Compras | MVP 1 |
| D08 | Clientes | Registrar destinatarios o clientes comerciales. | Mantenimiento de RUC/DNI, direcciones de entrega georreferenciadas, ventanas horarias de atención. | Ventas / Servicio | MVP 1 |
| D09 | Transportistas | Gestionar empresas de transporte de terceros o flota propia. | Registro de RUC, MTC habilitación, contratos, tarifas y asignación de unidades. | Transporte | MVP 1 |
| D10 | Vehículos | Registrar unidades de transporte (camiones, furgones, motos). | Ficha técnica de vehículo, placa, marca, cubicaje, carga útil, vencimiento de SOAT/CITV. | Transporte | MVP 1 |
| D11 | Conductores | Administrar personal de conducción. | Registro de DNI, Licencia de Conducir, categoría, vencimiento y estado de habilitación. | Transporte | MVP 1 |
| D12 | Compras | Gestionar requerimientos y solicitudes de abastecimiento. | Registro de Requerimientos de Compra, solicitudes de cotización y cuadros comparativos. | Compras | MVP 2 |
| D13 | Recepción de Mercadería | Controlar el ingreso físico de bienes a almacén. | Registro de Citas de Ingreso, Control de Puerta (Garita), Actas de Recepción e ingreso vs Orden de Compra. | Recepción / Garita | MVP 2 |
| D14 | Control de Calidad | Verificar el cumplimiento de especificaciones físicas/sanitarias. | Inspección de lotes recibidos, muestreo, registro de no conformidades, pase a cuarentena o liberación. | Inspector Calidad | MVP 2 |
| D15 | Inventario | Mantener el saldo de existencias y sus movimientos. | Cálculo en tiempo real de stock por SKU/Ubicación/Lote/Serie. Control de Kardex inmutable. | Inventariador | MVP 2 |
| D16 | Trazabilidad | Rastrear el historial completo de cada unidad o lote. | Genealogía de lotes, trazabilidad ascendente y descendente (desde recepción hasta entrega al cliente). | Auditor / Calidad | MVP 2 |
| D17 | Pedidos de Salida | Registrar órdenes de despacho o requerimientos internos. | Validación de crédito/autorización, reserva de stock y generación de órdenes de picking. | Despachador | MVP 2 |
| D18 | Picking | Gestionar la recolección física de productos en almacén. | Generación de listas de picking optimizadas por ruta interna de pasillos, confirmación de lote recolectado. | Picker / Almacén | MVP 2 |
| D19 | Packing | Consolidar y empaquetar los ítems recolectados. | Verificación de ítems recolectados, embalaje en cajas/pallets (Unidades Logísticas/LPN) y etiquetado. | Packer | MVP 2 |
| D20 | Despacho | Preparar la carga para su salida del almacén. | Verificación de carga en muelle, emisión de Guía de Remisión y Acta de Despacho. | Despachador | MVP 2 |
| D21 | Transporte | Coordinar el transporte de larga distancia o reparto local. | Consolidación de carga en viajes, asignación de vehículo/conductor y emisión de manifiesto. | Transportista | MVP 3 |
| D22 | Planificación de Rutas | Diseñar la secuencia de paradas de entrega. | Secuenciamiento de entregas, ventanas horarias, restricciones de tráfico y cálculo de distancia. | Planificador | MVP 3 |
| D23 | Seguimiento GPS | Monitorear la ubicación de los vehículos en ruta. | Recepción de coordenadas GPS (móvil/telemetría), cálculo de ETA y detección de eventos geocerca. | Monitoreo GPS | MVP 3 |
| D24 | Entrega | Confirmar el traspaso físico de la mercadería al cliente. | Prueba de Entrega Digital (POD): captura de firma en pantalla, foto de recepción u OTP SMS. | Conductor | MVP 3 |
| D25 | Devoluciones | Procesar el retorno de mercadería no entregada o rechazada. | Registro de Autorización de Devolución (RMA), recepción en almacén de devoluciones y reingreso a stock. | Recepción | MVP 3 |
| D26 | Incidencias | Registrar eventos anómalos durante el ciclo logístico. | Registro de roturas, faltantes, siniestros, retrasos y bloqueos en ruta con evidencias fotográficas. | Operaciones | MVP 3 |
| D27 | Gestión Documental | Emitir, almacenar y validar documentos logísticos. | Generación de PDFs (Guías, Manifiestos, Actas), firmado digital interno y control de versiones. | Sistema | MVP 1 |
| D28 | KPIs | Generar métricas e indicadores de desempeño operativo. | Cálculo de OTIF (On-Time In-Full), Exactitud de Registro de Inventario (ERI), Rotación y Tiempos de Ciclo. | Gerencia | Consolidación |
| D29 | Integraciones Externas | Interconectar con servicios públicos y plataformas de terceros. | Consultas RUC (SUNAT), Padrones, Verificación de Licencias (MTC), Geocodificación y SMS/OTP. | Sistema / API | MVP 1 |
| D30 | Auditoría | Mantener la trazabilidad de seguridad de todas las operaciones. | Registro append-only de eventos del sistema, dirección IP, sesión, score biométrico y cambios. | Auditor | MVP 1 |
| D31 | Seguridad y Permisos | Enforzar el control de acceso y autenticación continua. | Validación de permisos RBAC por endpoint, verificación de score de riesgo biométrico y step-up OTP. | Seguridad | MVP 1 |
| D32 | Notificaciones | Alertar a usuarios sobre eventos críticos o tareas pendientes. | Envío de alertas por email, SMS o push sobre desvíos de ruta, rechazos, stock bajo y aprobaciones pendientes. | Sistema | MVP 3 |

---

## Estructura de Cada Dominio

Para cada uno de los 32 dominios se aplicará el estándar de arquitectura funcional:
- **Entidades Propietarias:** Definidas en el catálogo conceptual.
- **Acciones Sensibles:** Acciones que requieren re-autenticación o Step-up OTP.
- **Modo de Auditoría:** Registro de creación, actualización, anulación y cambio de estado con marca de tiempo e IP.
