# 36. Contrato para Fase 039

`GET /unloading-operations/{id}/receiving-scan-preparation` solo responde cuando descarga está completada. Entrega referencias de OC, líneas/cantidades esperadas, documentos, contexto de precinto y responsables.

No contiene cantidades recibidas ni comandos de recepción. `receiving_capabilities_future` marca explícitamente el handoff futuro.

