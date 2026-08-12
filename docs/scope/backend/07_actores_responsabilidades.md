# 07. Actores y Matriz de Permisos — Proyecto T1

## 1. Definición de Actores del Backend

| Código Actor | Nombre del Actor | Descripción Funcional | Áreas de Acceso Permitiadas |
|---|---|---|---|
| `ACT_ADM` | Administrador | Gestión de configuración global, seguridad y catálogo de maestros. | Todos los dominios y configuraciones. |
| `ACT_GER` | Gerencia Logística | Supervisión de KPIs, aprobación de compras de alto valor y reportes. | KPIs, Auditoría, Aprobaciones de Compra. |
| `ACT_CMP` | Comprador | Creación de requerimientos, solicitudes de cotización u órdenes. | Compras, Proveedores, Productos. |
| `ACT_APROB`| Aprobador de Compras | Autorización formal de órdenes de compra. | Aprobaciones, Cuadros Comparativos. |
| `ACT_GAR` | Guardia (Garita) | Registro de ingresos/salidas de vehículos en planta. | Control de Puerta (Ingresos/Salidas). |
| `ACT_REC` | Recepcionista Almacén | Descarga de vehículos, conteo físico inicial y actas. | Recepción, Citas, Inbound. |
| `ACT_CAL` | Inspector de Calidad | Evaluación física/organoléptica, pase a cuarentena o liberación. | Calidad, Cuarentena, Liberaciones. |
| `ACT_ALM` | Almacenero | Ubicación de productos (Putaway), reabastecimiento, kardex. | Ubicaciones, Kardex, Transferencias. |
| `ACT_PIC` | Picker | Recolección de productos según lista de picking. | Picking Tasks. |
| `ACT_PAC` | Packer | Empaque de ítems, pesado y etiquetado LPN. | Packing Units. |
| `ACT_DES` | Despachador | Verificación de carga en muelle y emisión de Guía de Remisión. | Despachos, Guías de Remisión. |
| `ACT_PLN` | Planificador de Rutas | Consolidación de viajes, asignación de ruta y vehículos. | Rutas, Viajes, Asignación Vehicular. |
| `ACT_CND` | Conductor (Chofer) | Conducción, reporte GPS y registro de Prueba de Entrega (POD). | App Móvil, GPS, Entregas, Incidencias. |
| `ACT_AUD` | Auditor de Seguridad | Verificación inmutable de logs de auditoría y score biométrico. | Logs de Auditoría, Eventos de Riesgo. |
| `ACT_CLI` | Cliente Receptor | Consulta del estado del pedido y firma/OTP de conformidad. | Vista de Rastreo Externa, POD. |
| `ACT_SYS` | Sistema (Workers) | Tareas asíncronas de fondo (PDF, alertas, cálculo KPIs). | Servicios Internos Asíncronos. |

---

## 2. Separación de Funciones (Segregation of Duties - SoD)

Para prevenir fraude y errores en la cadena logística, el backend impondrá las siguientes reglas de separación de funciones:

1. **El Comprador (`ACT_CMP`) NO puede aprobar su propia Orden de Compra (`ACT_APROB`).**
2. **El Recepcionista (`ACT_REC`) NO puede realizar el Control de Calidad (`ACT_CAL`) de la misma recepción.**
3. **El Inspector de Calidad (`ACT_CAL`) NO puede realizar la Ubicación física en stock disponible (`ACT_ALM`).**
4. **El Picker (`ACT_PIC`) NO puede realizar la auditoría de Packing (`ACT_PAC`) de la misma orden.**
5. **El Conductor (`ACT_CND`) NO puede anular Guías de Remisión ni modificar la ruta asignada.**
