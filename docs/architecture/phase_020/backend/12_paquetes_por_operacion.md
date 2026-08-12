# 12. Paquetes por Operación

Para simplificar la administración física, es posible exportar de manera unificada todos los documentos que intervienen en una operación de almacén (ej. una Recepción de Mercadería).

## Reglas de Inclusión
Al solicitar el paquete para un ID de operación se exportan:
- **Cita (CIT)**
- **Control de Puerta (CPV)**
- **Acta de Recepción (AREC)**
- **Nota de Ingreso (NI)**
- **Acta de Diferencias (DIF)** si aplica.
- **No Conformidades (NC)** si aplica.

El archivo ZIP se genera dinámicamente incluyendo manifiestos y checksums.
