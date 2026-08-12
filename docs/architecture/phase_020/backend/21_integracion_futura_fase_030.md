# 21. Integración Futura con Fase 030

La Fase 030 abordará los flujos reales de inventario y cuadre físico de almacén.

## Puntos de Contacto
- **Confirmación de NI (Nota de Ingreso)**: Al confirmarse una NI, el sistema leerá el snapshot inmutable del documento para registrar el incremento físico de stock y alimentar la base del Kardex.
- **Cuarentena en NC (No Conformidad)**: Un lote marcado como rechazado en el snapshot de la NC generará un bloqueo automático de stock a nivel de base de datos.
