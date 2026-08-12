# 14. Idempotencia y Concurrencia

Para evitar la duplicación de documentos bajo alta concurrencia en la red o clicks repetidos del operador, el backend implementa mecanismos atómicos.

## Soluciones Técnicas
- **Bloqueo a nivel de fila (`with_for_update`)**: Utilizado al reservar el correlativo dentro de la transacción de base de datos para impedir que otra solicitud asigne el mismo número.
- **Claves de Idempotencia**: La API de emisión acepta un encabezado `X-Idempotency-Key` o un parámetro en el cuerpo. Si se recibe una petición con la misma llave para un documento ya emitido, se retorna la respuesta guardada sin ejecutar la lógica de reserva de serie de nuevo.
