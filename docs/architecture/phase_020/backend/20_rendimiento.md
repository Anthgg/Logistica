# 20. Rendimiento y Optimización

Medidas implementadas para garantizar la escalabilidad bajo alta carga transaccional:

## Estrategias
- **Procesamiento de PDF ligero**: El renderer WeasyPrint es invocado usando el pool de templates compilados con Jinja2 en memoria para evitar accesos al disco en lecturas sucesivas.
- **Bloqueos eficientes**: El bloqueo de correlativo se ejecuta solo durante la fase final de emisión, abarcando una transacción extremadamente corta que no excede los 100ms.
- **Exportación en lote**: Exportaciones mayores a 10 elementos se encolan para procesamiento asíncrono para evitar bloquear el hilo del servidor HTTP.
