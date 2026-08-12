# Snapshot

El snapshot canónico reúne aviso, revisión confirmada, referencias de OC, líneas esperadas, allocations, proveedor, transportista, vehículo, conductor, documentos, carga, slot, zona horaria y requisitos especiales.

Los UUID, fechas y `Decimal` se serializan de forma estable antes de calcular SHA-256. El documento CIT y el paquete conservan la referencia al snapshot que los originó.

Los cambios posteriores en maestros no reescriben un snapshot congelado.
