# F004 · Aceptación en navegador

## Estado: NO PREPARADO

El gate técnico previo a la UAT humana **no se ha superado**, así que no se ha montado
runtime F004 ni se ha convocado al usuario. Pedirle que pruebe «crear almacén» hoy sería
pedirle que confirme una pantalla que no existe.

## Runtime actual (no es runtime F004)

| | |
|---|---|
| Backend mount | `C:/Users/anthg/logistica-main/backend/app` |
| Backend SHA | `c421dcc` (idéntico al head F004: `git diff origin/main` vacío) |
| Frontend proceso | PID 22444, `C:/Users/anthg/logisticaf-main` |
| Frontend SHA | `8dcf23b` (idéntico al head F004) |

El runtime sirve código byte a byte igual al head F004 porque F004 aún no tiene cambios.
Por eso las sondas de esta auditoría son válidas como observación del head F004. En cuanto
se aplique el primer arreglo habrá que remontar el runtime sobre
`C:/Users/anthg/Logistica-F004` y `C:/Users/anthg/LogisticaF-F004` y volver a registrar la
identidad completa antes de convocar al usuario.

## Superficies exigidas por el pedido

| # | Superficie | Preparada | Motivo |
|---|---|---|---|
| A | Organizaciones | sí | `/logistics/organizations` operativa |
| B | Editar organización | sí, con reserva | diálogo completo; el botón de estado de la misma tabla tiene el defecto de fila equivocada |
| C | Sedes | sí | `/logistics/branches` con selector de organización |
| D | Desactivar sede | sí | botón por fila, `row.id` correcto |
| E | Almacenes | **no** | listado siempre vacío |
| F | Crear almacén | **no** | no existe UI |
| G | Persistencia con F5 | parcial | comprobable en A–D, no en E–F |
| H | Sesión | sí | 401 `SESSION_REQUIRED` verificado sin sesión |
| I | Network | — | pendiente del runtime F004 |
| J | Console | — | pendiente del runtime F004 |
| K | Negative path | **no** | sin tests HTTP F004 que los cubran |

## Evidencia recogida (solo lectura, sin sesión de navegador)

Sondas ejecutadas dentro del contenedor con `TestClient` y `dependency_overrides`,
únicamente `GET`, sin escribir en la base:

```
GET /api/logistics/organizations                      -> 200  dict:items,page,page_size,total,total_pages
GET /api/logistics/organizations/{id}                 -> 200  OrganizationResponse
GET /api/logistics/organizations/{id}/branches        -> 200  dict:items,...   (org ORG-c65050, 1 sede)
GET /api/logistics/branches/{id}                      -> 200  BranchResponse
GET /api/logistics/branches/{id}/warehouses           -> 200  {"items":[],...}
GET /api/logistics/warehouses                         -> 200  []      <-- array desnudo, y vacío
GET /api/logistics/warehouses/{id_real}               -> 404  RESOURCE_NOT_FOUND
GET /api/logistics/organizations   (sin sesión)       -> 401  SESSION_REQUIRED
GET /api/logistics/warehouses      (sin sesión)       -> 401  SESSION_REQUIRED
```

Estas sondas sustituyen dependencias de autenticación; **no** son una prueba de extremo a
extremo con sesión real de navegador, y no se presentan como tal.

## Qué falta antes de convocar la UAT

1. Publicar creación y edición estructural de almacén (backend y navegador).
2. Reparar el contrato del listado de almacenes (array vs paginado) o paginar el endpoint.
3. Poblar `organization_id` en la creación y decidir qué hacer con las 3 filas huérfanas.
4. Corregir el `server_default` con comillas y el `warehouse_type` corrupto.
5. Corregir `editing?.id ?? org.id` en organizaciones.
6. Cablear «Nueva sede».
7. Tests HTTP de regresión y gate CI con nombre honesto.
8. Remontar runtime sobre los worktrees F004 y registrar identidad completa.
