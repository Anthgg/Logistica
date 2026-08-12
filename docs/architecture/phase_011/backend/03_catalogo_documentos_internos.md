# 03 — Catálogo de Documentos Internos (REQ a DEV)

## Matriz de 28 Tipos Documentales Internos

| Código | Nombre | Familia | Módulo Propietario | Sensible | QR | Firma |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ** | Requerimiento de compra | `PURCHASING` | `purchases` | `False` | `False` | `True` |
| **SCOT** | Solicitud de cotización | `PURCHASING` | `purchases` | `False` | `False` | `False` |
| **CCO** | Cuadro comparativo | `PURCHASING` | `purchases` | `True` | `False` | `True` |
| **OC** | Orden de compra | `PURCHASING` | `purchases` | `True` | `True` | `True` |
| **CIT** | Cita de recepción | `INBOUND` | `inbound` | `False` | `True` | `False` |
| **CPV** | Control de puerta vehicular | `INBOUND` | `gate_control` | `True` | `False` | `True` |
| **AREC** | Acta de recepción | `INBOUND` | `receptions` | `False` | `True` | `True` |
| **NI** | Nota de ingreso | `INBOUND` | `receptions` | `False` | `True` | `True` |
| **DIF** | Acta de diferencias | `INBOUND` | `receptions` | `True` | `True` | `True` |
| **NC** | No conformidad | `QUALITY` | `quality` | `True` | `True` | `True` |
| **PUT** | Orden de ubicación | `INVENTORY` | `inventory` | `False` | `True` | `False` |
| **MOV** | Movimiento de almacén | `INVENTORY` | `inventory` | `False` | `False` | `False` |
| **AJI** | Acta de ajuste de inventario | `INVENTORY` | `inventory` | `True` | `True` | `True` |
| **CNT** | Acta de conteo | `INVENTORY` | `inventory` | `False` | `True` | `True` |
| **TRA** | Orden de transferencia | `INVENTORY` | `inventory` | `False` | `True` | `True` |
| **PED** | Pedido de salida | `OUTBOUND` | `outbound` | `False` | `False` | `False` |
| **ODS** | Orden de salida | `OUTBOUND` | `outbound` | `False` | `True` | `True` |
| **PICK** | Lista de picking | `OUTBOUND` | `picking` | `False` | `True` | `False` |
| **PACK** | Packing list | `OUTBOUND` | `packing` | `False` | `True` | `False` |
| **MAN** | Manifiesto de carga | `DISPATCH` | `dispatches` | `False` | `True` | `True` |
| **ADSP** | Acta de despacho | `DISPATCH` | `dispatches` | `False` | `True` | `True` |
| **HV** | Hoja de viaje | `TRANSPORT` | `trips` | `False` | `True` | `True` |
| **HR** | Hoja de ruta | `TRANSPORT` | `routes` | `True` | `True` | `False` |
| **INC** | Reporte de incidencia | `TRANSPORT` | `incidents` | `False` | `False` | `False` |
| **POD** | Prueba de entrega | `DELIVERY` | `deliveries` | `True` | `True` | `True` |
| **EP** | Acta de entrega parcial | `DELIVERY` | `deliveries` | `True` | `True` | `True` |
| **RECH** | Acta de rechazo | `DELIVERY` | `deliveries` | `True` | `True` | `True` |
| **DEV** | Autorización de devolución | `REVERSE_LOGISTICS` | `returns` | `False` | `True` | `True` |
