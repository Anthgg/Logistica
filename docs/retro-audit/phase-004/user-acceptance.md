# F004 · Aceptación de usuario

## USER_ACCEPTANCE = PENDING

No se ha ejecutado ninguna ronda de UAT y no se declara ningún PASS en nombre del
usuario.

## Estado del gate técnico previo

| Owner gap | Estado |
|---|---|
| Organization edit | **TECHNICAL PASS** — `PATCH /organizations/{id}` con permiso y ámbito, diálogo funcional, test de persistencia |
| Branch deactivate | **TECHNICAL PASS** — `PATCH /branches/{id}/status`, persiste, reactivación probada, conflicto 409 con almacén activo |
| Warehouse create | **TECHNICAL PASS** — ruta estructural, `organization_id` derivado de la sede, UI publicada con selectores humanos |

| Blocker nuevo | Estado |
|---|---|
| Organization status, fila equivocada | **FIXED** — con test de la secuencia exacta |
| Branch create sin UI | **FIXED** — crea y edita |
| Contrato de almacenes desalineado | **FIXED** — DTO copiado del real, sin listado global inventado |
| RBAC en rutas F004 | **FIXED** — catálogo existente aplicado |
| Aislamiento por tenant | **FIXED** — derivado de datos persistidos |
| Almacén huérfano al crear | **FIXED** — en los tres escritores activos |
| Corrupción de defaults | **FIXED** — migración `hj460110046dk` |
| Huérfanos heredados | **BLOCKED** — `LEGACY_ORPHAN_REQUIRES_DATA_DECISION`, sin evidencia de propiedad |

## Lo que NO he podido comprobar

El precheck de navegador de las pantallas autenticadas **no está hecho**. Iniciar
sesión exige escribir credenciales, y eso lo hace el usuario, no yo. Lo verificado
sin sesión: la aplicación arranca, la ruta protegida redirige al login, y la consola
solo muestra los 401 esperados del sondeo de sesión — sin crash de React, sin 404
ni 500 inesperados.

La evidencia equivalente más fuerte de la que dispongo son los 44 casos HTTP que
atraviesan router y dependencias con RBAC real sembrado. No sustituyen la prueba
humana y no se presentan como tal.

## Guion de la primera ronda

Runtime servido desde los worktrees F004 (identidad registrada en
[browser-acceptance.md](browser-acceptance.md)).

### A · Organizaciones
1. Abrir `/logistics/organizations`. La tabla carga.
2. Editar una organización: cambiar el nombre a algo temporal.
3. Guardar → 2xx.
4. F5 → el cambio persiste.
5. Devolver el nombre original.

### B · Estado de organización
6. Abrir el editor de la organización A y cerrarlo con Cancelar.
7. Pulsar Desactivar en la organización **B**.
8. En Network, comprobar que el PATCH va contra el id de **B**, no el de A.
9. **Esperado: 403 `STEP_UP_REQUIRED`**, mostrado como «Esta acción requiere
   verificación adicional de tu identidad». No es un fallo: ese permiso está
   catalogado como crítico con step-up y F004 no lo relaja. Lo que se valida aquí es
   que la petición apunta a la fila correcta y que el error se muestra sin romper nada.

### C · Sedes
10. Abrir `/logistics/branches`.
11. Elegir una organización en el selector.
12. Crear una sede UAT: código `UAT-F004-SEDE`, nombre `Sede UAT F004`.
13. Editarla (cambiar el nombre) y guardar.
14. Desactivarla → 2xx.
15. F5 → sigue inactiva.

### D · Almacenes
16. Abrir `/logistics/warehouses`.
17. Elegir organización en el selector (nombre y código, sin UUID).
18. Elegir sede en el segundo selector.
19. «Nuevo almacén»: código `UAT-F004-WH-001`, nombre `Almacén UAT F004`, tipo
    General, dirección/distrito/provincia/departamento.
20. Guardar → 201.
21. Aparece en el listado.
22. F5 → sigue presente.
23. Abrir «Ficha» → el detalle muestra la organización y la sede correctas.

El código debe ser **globalmente único**: la tabla tiene un UNIQUE global sobre
`code`, no solo por sede.

### E · Rutas negativas
24. Crear otro almacén con el mismo código → 409 mostrado como error legible.
25. Enviar el formulario sin nombre → validación, sin petición.
26. Intentar desactivar una sede que tenga un almacén activo → 409 legible.

### F · Seguridad
27. La sesión se mantiene entre recargas.
28. Network: 0 respuestas 500.
29. Consola: 0 crashes de React.

## Registro de rondas

| Ronda | Fecha | Resultado | Defectos |
|---|---|---|---|
| — | — | no ejecutada | — |
