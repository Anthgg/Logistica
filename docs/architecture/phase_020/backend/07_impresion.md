# 07. Registro de Impresión

La impresión física de documentos logísticos es tratada como un evento de seguridad crítico.

## Registro de Intención
- Cada vez que el frontend solicita enviar el documento a la impresora, el backend registra el evento `logistics.document.print_requested`.
- Se incrementa el contador `print_request_count` en la base de datos de manera atómica.
- Se capturan metadatos del cliente (IP, agente de usuario, terminal física) para propósitos de auditoría de fraude.
