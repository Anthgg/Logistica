# 04. Flujos Operativos y Diagramas de Estado — Proyecto T1

## Flujo 1: Compras y Abastecimiento

Requerimiento de compra → cotización → evaluación → aprobación → orden de compra.

```mermaid
graph TD
    A[Requerimiento Creado: DRAFT] -->|Enviar a revisión| B[Requerimiento: PENDING_APPROVAL]
    B -->|Aprobar| C[Requerimiento: APPROVED]
    B -->|Rechazar| D[Requerimiento: REJECTED]
    C -->|Solicitar Cotizaciones| E[Solicitud Cotización: SENT]
    E -->|Registrar Ofertas| F[Cotizaciones Recibidas: EVALUATING]
    F -->|Generar Cuadro Comparativo| G[Cuadro Comparativo: READY]
    G -->|Aprobar Proveedor| H[Orden de Compra: DRAFT]
    H -->|Aprobación de Compra - Step-Up| I[Orden de Compra: ISSUED]
    I -->|Confirmación Proveedor| J[Orden de Compra: CONFIRMED]
```

### Reglas de Negocio
- Compras mayores a $5,000 USD requieren aprobación por Gerencia de Operaciones y Step-up OTP del aprobador.
- La Orden de Compra emitida es **irreversible** y bloquea la modificación de precios.

---

## Flujo 2: Ingreso a Planta y Control de Garita

Aviso de llegada → control de puerta → asignación de muelle → descarga → recepción → diferencias.

```mermaid
sequenceDiagram
    autonumber
    actor C as Conductor / Transportista
    participant G as Control Puerta (Garita)
    participant A as Almacén / Muelle
    participant S as Sistema Backend API

    C->>G: Presenta DNI/Placa/Guía Remisión
    G->>S: GET /api/logistics/inbound-appointments?plate={placa}
    S-->>G: Cita Registrada Validada
    G->>S: POST /api/logistics/gate-entries (Estado: IN_GATE)
    S-->>G: Ticket de Ingreso Generado
    A->>S: POST /api/logistics/dock-assignments (Asignar Muelle 03)
    S-->>A: Muelle Asignado
    A->>S: POST /api/logistics/receptions (Estado: UNLOADING)
    A->>S: POST /api/logistics/receptions/{id}/items (Conteo Físico)
    alt Existen Diferencias (Faltantes / Dañados)
        S->>S: Generar Acta de Discrepancias (Estado: COMPLETED_WITH_DISCREPANCIES)
    else Conteo Exacto
        S->>S: Estado: COMPLETED_OK
    end
```

---

## Flujo 3: Control de Calidad y Ubicación en Almacén

Recepción → control de calidad → cuarentena → liberación → ubicación → stock disponible.

```mermaid
graph TD
    A[Mercadería Recibida] --> B{¿Requiere Inspección?}
    B -- Sí --> C[Estado: IN_QUALITY_INSPECTION / CUARENTENA]
    B -- No --> F[Estado: PENDING_PUTAWAY]
    C --> D[Muestra Evaluada por Inspector]
    D -->|Aprobado| E[Pase a Liberación - Step-Up]
    D -->|Rechazado| G[Estado: NON_CONFORMANT / REJETED]
    E --> F
    F --> H[Asignación Ubicación Interna: PASILLO-RACK-CAJA]
    H --> I[Confirmación de Ubicación por Almacenero]
    I --> J[Stock Disponible para Venta/Salida]
```

---

## Flujo 4: Salida de Almacén, Picking y Packing

Pedido de salida → reserva → picking → packing → orden de salida → despacho.

```mermaid
graph TD
    A[Pedido de Salida: CREATED] --> B[Validación de Saldo y Reserva: STOCK_RESERVED]
    B --> C[Generación Orden de Picking: PICKING_PENDING]
    C --> D[Picking en Proceso: PICKING_IN_PROGRESS]
    D --> E[Confirmación de Conteo e Ítems: PICKING_COMPLETED]
    E --> F[Mesa de Packing: PACKING_IN_PROGRESS]
    F --> G[Empaque, Pesaje y Etiquetado LPN: PACKED]
    G --> H[Zona de Despacho / Staging: READY_FOR_DISPATCH]
```

---

## Flujo 5: Transporte, Ruta Real y Seguimiento GPS

Despacho → planificación de ruta → asignación de vehículo → viaje → GPS → entrega.

```mermaid
sequenceDiagram
    autonumber
    actor P as Planificador
    participant S as Backend API
    actor D as Conductor (App Móvil)
    actor R as Cliente Receptor

    P->>S: POST /api/logistics/trips (Asignar Ruta + Vehículo + Conductor)
    S-->>P: Viaje Registrado (Estado: SCHEDULED)
    D->>S: POST /api/logistics/trips/{id}/start (Inicia Ruta)
    S-->>D: Viaje Estado: IN_TRANSIT
    loop Cada 30 Segundos
        D->>S: POST /api/logistics/gps-positions (Lat, Lng, Velocidad)
        S->>S: Evaluar Geocercas y Alertas
    end
    D->>S: POST /api/logistics/deliveries/{id}/arrived (Llegada a Parada)
    D->>R: Entrega Carga y Solicita Firma/OTP
    D->>S: POST /api/logistics/deliveries/{id}/complete (POD Foto + Firma + OTP)
    S-->>D: Entrega Confirmada (Estado: DELIVERED)
```

---

## Flujo 6: Incidencias, Rechazos y Devoluciones

Entrega parcial o rechazo → incidencia → devolución → inspección → disposición.

```mermaid
graph TD
    A[Cliente Rechaza Total / Parcialmente] --> B[Conductor Registra Incidencia: LOGISTIC_INCIDENT_CREATED]
    B --> C[Captura Foto Evidencia + Motivo]
    C --> D[Generación RMA Autorización Devolución]
    D --> E[Retorno de Mercadería en Vehículo a Almacén]
    E --> F[Recepción de Devolución en Almacén]
    F --> G[Inspección de Estado: RE-STOCK / MERMA / REPARACIÓN]
```

---

## Flujo 7: Ciclo de Vida Documental

Operación logística → generación documental → emisión → descarga → reimpresión o anulación.

```mermaid
graph TD
    A[Operación Logística Completada] --> B[Solicitud Generación Documento]
    B --> C[Motor PDF Genera Documento Snapshot + HASH]
    C --> D[Subida a Cloud Storage: FILE_STORED]
    D --> E[Estado: ISSUED / EMITIDO]
    E -->|Consulta Usuario| F[Descarga PDF / Vista Previa]
    E -->|Solicitud Anulación| G{¿Requiere Step-Up?}
    G -- Sí --> H[Verificación OTP / Score Biométrico]
    H -->|Aprobado| I[Estado: ANNULLED / ANULADO + Auditoría]
    H -->|Fallado| J[Operación Bloqueada]
```
