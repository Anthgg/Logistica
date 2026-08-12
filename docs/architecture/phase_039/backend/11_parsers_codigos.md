# 11 parsers codigos

## Decisión

Se admiten identificadores internos, GTIN, Code 128, GS1 y QR interno como datos. Nunca se abre una URL ni se ejecuta contenido.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

