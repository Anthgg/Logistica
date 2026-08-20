# Gates de CI

Todos corren en el job `lint-and-test` y fallan el build. Ninguno es informativo.

| Gate | Falla si |
|---|---|
| Referencias desconocidas | El código exige un permiso que no existe en el catálogo |
| Duplicados | Hay códigos repetidos, o que solo difieren en mayúsculas |
| Metadata | A un permiso le falta alguna de las siete claves obligatorias |
| Convención | Un código no cumple `<dominio>.<recurso>.<accion>` en minúsculas |
| Step-up | Un permiso con `requires_step_up` no tiene política |
| Matriz de roles | No cubre exactamente los roles de sistema, hay uno vacío, o concede permisos inexistentes |
| Públicos | Aparece un endpoint sin autenticación fuera de la lista declarada |
| Mutaciones sin permiso | Una mutación de negocio queda solo con sesión sin justificación escrita |
| Artefacto derivado | `permission_catalog.json` deja de corresponder al catálogo |
| Identidad | Vuelve `x_actor_id` o un UUID fijo de respaldo |
| Rol de plataforma | Reaparece `user.role == "admin"` como autorización en el dominio logístico |

Más las **25 guardas de pytest** de `test_logistics_f006_catalog_gates.py` y las 30 de
PR 1 en `test_logistics_f006_endpoint_authorization.py`.

## Trinquetes

Los umbrales son monotónicos y están declarados en el código, no en la configuración:

```python
MAX_SENSITIVE_BASELINE = 0     # mutaciones de negocio solo con sesión, sin justificar
```

Un umbral que admite el valor actual «por ahora» acaba siendo permanente. Estos solo
pueden bajar, y el auditor avisa cuando podrían bajarse.

## Por qué dos redes

Las guardas de pytest y los guards en shell comprueban lo mismo por caminos distintos.
No es redundancia gratuita: un `-k` mal puesto, un fichero renombrado o un `xfail`
desactivan pytest sin que nadie lo note. El guard en shell no depende de la suite.

## Lo que un gate verde no dice

CI ejecuta gates dirigidos, no la suite completa. La suite completa tiene **139 fallos
en `main`** por un choque de mappers de SQLAlchemy: `PurchaseOrderModel` está declarado
en dos módulos. Es deuda anterior a F006 y no se arregla aquí, pero conviene no leer el
verde de CI como «toda la suite pasa».
