# 03. Snapshots Inmutables

Los datos utilizados para generar un documento son capturados en formato JSONB dentro del modelo `DocumentSnapshotModel` al momento de la emisión.

## Reglas de Inmutabilidad
- **Payload normalizado**: El JSONB se guarda ordenando las llaves alfabéticamente antes de serializar, garantizando un hash determinista.
- **Sin datos mutables**: Los cambios posteriores en los datos maestros (ej. cambio de nombre del cliente o dirección del almacén) no afectan al documento emitido, el cual siempre se renderiza desde su snapshot inmutable original.
- **Prevención de fugas**: Las credenciales, tokens temporales o contraseñas se eliminan explícitamente del snapshot antes del guardado.
