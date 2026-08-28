# Códigos automáticos de entidad

Fuente canónica: `backend/app/modules/logistics/organization/code_generator.py`.

## Formato

| Entidad | Prefijo | Ejemplo |
|---|---|---|
| Organización | `ORG` | `ORG000001` |
| Sede (branch) | `SED` | `SED000042` |
| Almacén | `ALM` | `ALM000117` |

Prefijo de 3 + secuencia de 6 dígitos con relleno de ceros = 9 caracteres. Cabe de sobra
en los `varchar(30)` de las tres tablas y bajo el límite de 20 de F022.

**Sin guiones.** No es una elección estética: `WAREHOUSE_CODE_REGEX` de F022 es
`^[A-Z0-9]{2,20}$` y un `ALM-000117` sería rechazado por una validación que ya estaba en
producción.

## Seguridad ante concurrencia

El contador vive en `entity_code_counters` (una fila por tipo de entidad) y se reserva
con bloqueo de fila:

```python
counter = db.scalars(
    select(EntityCodeCounter)
    .where(EntityCodeCounter.entity_type == entity_type)
    .with_for_update()
).first()
```

`FOR UPDATE` serializa a las peticiones concurrentes exactamente en ese punto: la
segunda espera a que la primera confirme antes de leer `next_value`. Dos altas
simultáneas no pueden leer el mismo número.

En la primera creación de un tipo la fila no existe todavía; si dos transacciones
intentan insertarla a la vez, la perdedora vuelve a leer **con bloqueo** en lugar de
propagar el error de unicidad.

Esto está probado, no supuesto: `tests/test_logistics_f0051_entity_codes_http.py`
incluye una prueba de 20 hilos reales con su propia `SessionLocal()` por hilo, y exige
20 códigos distintos.

## Qué pasa con los códigos existentes

La migración siembra cada contador con `COUNT(*)+1` de su tabla. Los códigos manuales
anteriores se conservan tal cual; solo se garantiza que la secuencia nueva empieza por
encima del volumen existente.

## Frontend

`src/components/logistics/EntityCodeField.tsx`:

- **En alta**: muestra «Se generará automáticamente». No hay input.
- **En edición**: muestra el código real en `<code>`, solo lectura.

Deliberadamente **no** es un `<input disabled>`: un campo con aspecto de formulario
invita a intentar escribir en él. Es metadato, y se presenta como tal.
