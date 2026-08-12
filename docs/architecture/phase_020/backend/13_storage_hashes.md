# 13. Almacenamiento y Hash SHA-256

La integridad de cada documento PDF se audita de forma binaria mediante criptografía SHA-256.

## Flujo de Integridad
1. Al renderizar el PDF binario en memoria, se calcula su hash SHA-256 (`file_hash`).
2. El hash se almacena en el registro de `DocumentArtifactModel`.
3. Al descargar el archivo, el adaptador de almacenamiento lee el archivo y vuelve a calcular el hash SHA-256.
4. Si el hash calculado no coincide con el guardado en base de datos, la descarga se bloquea por alerta de manipulación física (temper-evident) y se emite una auditoría crítica.
