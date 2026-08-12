# 06. Estados de Negocio y Transiciones — Proyecto T1

## 1. Máquinas de Estado Principales

### Requerimiento de Compra (`PurchaseRequest`)
- `DRAFT`: Borrador en edición por el solicitante.
- `PENDING_APPROVAL`: Enviado a aprobación de presupuesto.
- `APPROVED`: Aprobado por el jefe del área.
- `REJECTED`: Rechazado con motivo obligatorio.
- `CANCELLED`: Cancelado por el usuario.

### Orden de Compra (`PurchaseOrder`)
- `DRAFT`: En elaboración por el comprador.
- `ISSUED`: Emitida y enviada al proveedor (requiere Step-up para emisión).
- `CONFIRMED`: Confirmada por el proveedor con fecha de entrega.
- `PARTIALLY_RECEIVED`: Recepción parcial en almacén.
- `CLOSED`: Recepción total completada.
- `ANNULLED`: Anulada con justificación registrada en auditoría.

### Recepción (`Reception`)
- `SCHEDULED`: Cita programada en muelle.
- `IN_GATE`: Vehículo ingresado a garita.
- `AT_DOCK`: Vehículo posicionado en muelle de descarga.
- `UNLOADING`: Descarga física y conteo en proceso.
- `QUALITY_CHECK`: Transferido a inspección de calidad.
- `COMPLETED`: Proceso de recepción finalizado exitosamente.
- `COMPLETED_WITH_DISCREPANCIES`: Finalizado con observaciones o faltantes.

### Pedido de Salida (`OutboundOrder`)
- `CREATED`: Registrado en el sistema.
- `STOCK_RESERVED`: Stock reservado atómicamente en PostgreSQL.
- `IN_PICKING`: Tarea de recolección en pasillos iniciada.
- `PICKED`: Recolección completada.
- `PACKED`: Empaquetado y etiquetado con LPN.
- `STAGED`: En zona de pre-despacho.
- `DISPATCHED`: Despachado e integrado en Guía de Remisión.
- `CANCELLED`: Cancelado (libera la reserva de stock atómicamente).

### Viaje de Distribución (`Trip`)
- `PLANNED`: Ruta y paradas consolidadas.
- `ASSIGNED`: Vehículo y conductor asignados.
- `IN_TRANSIT`: Conductor inició el viaje en la App Móvil.
- `DELIVERING`: Conductor realizando entrega en una parada.
- `COMPLETED`: Todas las entregas procesadas.
- `CLOSED`: Viaje cerrado administrativamente tras rendición.

### Entrega (`Delivery`)
- `PENDING`: Pendiente de arribo del vehículo.
- `ARRIVED`: Vehículo dentro de la geocerca del cliente.
- `DELIVERED`: Entrega total exitosa con POD registrado.
- `PARTIALLY_DELIVERED`: Entrega parcial con acta de devolución.
- `REJECTED`: Rechazo total por el cliente.
- `FAILED_ATTEMPT`: Intento fallido (cliente ausente / local cerrado).

---

## 2. Reglas Generales de Transición

1. **Inmutabilidad de Estados Finales:** Los estados `CLOSED`, `COMPLETED` y `ANNULLED` son nodos terminales. Ningún documento en estos estados puede ser modificado.
2. **Motivo Obligatorio:** Toda transición a estados de excepción (`REJECTED`, `ANNULLED`, `CANCELLED`, `FAILED_ATTEMPT`) exige un código de motivo predefinido y una explicación textual mínima de 15 caracteres.
3. **Step-Up:** Las anulaciones de órdenes o recepciones en estado `ISSUED` o `COMPLETED` requieren re-autenticación obligatoria del usuario con score biométrico válido o token OTP.
