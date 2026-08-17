# F004 · Aceptación en navegador

## Estado: PRECHECK EJECUTADO — UAT HUMANA PENDIENTE

El precheck lo ejecuté yo sobre una sesión que el usuario ya tenía iniciada. No
sustituye la UAT: no declaro ningún PASS en su nombre.

## Identidad del runtime

| | |
|---|---|
| Backend branch | `audit/retro-phase-004-backend` |
| Backend SHA | `795c6ad4d1edb85fcc9387a70a5ad507c26ea3ab` |
| Backend mount | `C:\Users\anthg\Logistica-F004\backend\app` → `/app/app` |
| Frontend branch | `audit/retro-phase-004-frontend` |
| Frontend SHA | `a70539da3c88cb0136486d751af67ce184d957cf` |
| Frontend proceso | `C:\Users\anthg\LogisticaF-F004\node_modules\...\vite.js`, raíz `LogisticaF-F004` |

El servicio de compose no monta `alembic/`, así que el contenedor arrancaba con
las revisiones de la imagen (construida desde main) y no encontraba
`hj460110046dk`. El runtime F004 usa un override de compose que añade ese montaje.
Vive en el scratchpad, no en el repositorio.

## Lo que el precheck encontró (dos defectos reales)

### 1 · 422 al crear almacén

```
POST /api/logistics/branches/{id}/warehouses -> 422
{"code":"VALIDATION_ERROR","details":[{"field":"branch_id","message":"Este campo es obligatorio."}]}
```

`LogisticsWarehouseCreate` exigía `branch_id` en el cuerpo aunque la sede viaja en
la ruta y el servicio deriva de ella la organización. El formulario, que hace lo
correcto, recibía 422 siempre.

Mis tests no lo detectaron porque el payload de prueba incluía `branch_id`, un
campo que la UI no envía. Corregido, y el helper usa ahora el cuerpo exacto del
formulario.

### 2 · El error de la API no se veía

Al repetir un código, el backend devuelve 409 y el diálogo seguía abierto, pero el
`Alert` se renderiza a nivel de página: **detrás del modal**. El usuario veía el
formulario intacto y ningún motivo. El `Alert` va ahora también dentro del diálogo,
en almacenes, sedes y organizaciones.

## Superficies comprobadas

| # | Superficie | Resultado |
|---|---|---|
| A | Organizaciones | **OK** — 120 registros, «Página 1 de 6 · 120 registros», acciones Editar/Desactivar visibles |
| B | Editar organización | diálogo disponible; el PATCH no se ejecutó en el precheck |
| B' | Estado de organización | no ejecutado en navegador; cubierto por 3 tests HTTP que separan step-up, persistencia y conflicto |
| C | Sedes | **OK** — carga con selector de organización y botón «Nueva sede» ya operativo |
| D | Desactivar sede | no ejecutado en navegador; cubierto por tests HTTP (desactiva, reactiva, 409 con almacén activo, 403 ajena) |
| E | Almacenes | **OK** — organización → sede → listado. «Página 1 de 1 · 1 registros», **sin NaN ni undefined** |
| F | Crear almacén | **OK** — 201, `UAT-F004-WH-001` visible en el listado |
| G | Persistencia F5 | **OK** — sigue presente tras recarga |
| H | Sesión | **OK** — se mantiene entre navegaciones; sin sesión, 401 `SESSION_REQUIRED` |
| I | Network | 401 (pre-login), 422 (defecto 1, corregido), 409 ×3 (duplicados). **0 respuestas 500** |
| J | Console | **0 crashes de React** |
| K | Detalle estructural | **OK** — `GET /branches/{id}/warehouses/{id}` → 200, muestra organización y sede por nombre |
| L | Código duplicado | **OK** — 409 controlado; el mensaje ya se ve dentro del diálogo |

## Invariante comprobado en base de datos

```
UAT-F004-WH-001 | org=2e24e22a-…  | branch=01b9f0bc-…  | status=ACTIVE | is_active=t | created_by=set
```

`organization_id` derivado de la sede, `status` e `is_active` coherentes,
`created_by` poblado. Es exactamente lo que fallaba antes.

## Lo que NO comprobé en navegador

Editar organización, cambiar su estado y desactivar una sede: sus mutaciones no se
ejecutaron desde el navegador. El panel del navegador renderiza la página a una
escala en la que los controles quedan a ~13 px entre sí y varios clics cayeron
donde no debían — de hecho uno de esos clics fue el que envió un formulario a
medias y destapó el 422. Con referencias del árbol de accesibilidad rellené el
formulario de almacén de forma fiable, pero no forcé el resto de mutaciones.

Están cubiertas por la suite HTTP, que atraviesa router y dependencias con RBAC
real. No es lo mismo que verlas en pantalla, y por eso siguen en el guion de UAT.

## Dato creado durante la sesión

Además de `UAT-F004-WH-001`, la tabla de sedes pasó de 114 a 115: aparece
`DDFF / prueba` en la organización PRUBEBA, creada a las 00:20 UTC. No la creé yo;
salió de la propia sesión del usuario mientras probaba el botón «Nueva sede»
recién habilitado. Se registra como cambio esperado, no como contaminación.
