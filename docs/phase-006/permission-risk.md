# Riesgo y step-up

## Niveles

| Nivel | Permisos | Criterio |
|---|---:|---|
| `low` | 215 | Lectura de catálogos y datos no sensibles |
| `medium` | 159 | Operación de negocio ordinaria |
| `high` | 145 | Ajustes, aprobaciones, datos sensibles |
| `critical` | 36 | Administración de RBAC, adjudicaciones, cierres irreversibles |

El riesgo se asigna por impacto, no por intuición: leer un catálogo de países es `low`
aunque el endpoint sea nuevo; registrar la decisión de adjudicación de una evaluación
es `critical` aunque escriba una sola fila, porque cierra el ciclo de selección de
proveedor.

## Step-up: una sola autoridad

Hasta F006 PR 2 había **dos** declaraciones independientes de qué operación exige
verificación reforzada, y discrepaban en las dos direcciones:

- 46 permisos marcados `requires_step_up=True` no tenían entrada en `POLICY_CATALOG`,
  de modo que `is_sensitive_permission` los consideraba no sensibles;
- 4 entradas del catálogo de políticas correspondían a permisos con
  `requires_step_up=False`, de modo que `require_permission` no les exigía prueba.

El efecto era que **una misma operación exigía step-up o no según cuál de los dos
guards protegiera el endpoint**.

Ahora `step_up_policy.py` es la autoridad:

```
permission_catalog  →  step_up_policy  →  seed  →  base de datos
   (declara)            (sintetiza)      (deriva)
```

Lo que el catálogo marca se sintetiza como política si falta, siguiendo la convención
de las 87 entradas escritas a mano —todas usan `combined_face_pad` y `fail_closed`—.
Las manuales conservan prioridad: expresan una elección deliberada de factores.

La siembra deriva de la política el valor que guarda en la base, así que las dos no
pueden volver a contradecirse. Dos listas que deben coincidir acaban divergiendo; una
lista con una derivación, no.

Resultado: 129 permisos con step-up, **129 con política**.

## Qué no cambió

Los TTL, el número de intentos y los factores disponibles son los de F005. F006 no crea
un segundo mecanismo de verificación reforzada; solo hace que una única lista decida
cuándo se aplica.
