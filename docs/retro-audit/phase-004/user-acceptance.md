# F004 · Aceptación de usuario

## USER_ACCEPTANCE = PENDING

No se ha ejecutado ninguna ronda de UAT y no se declara ningún PASS en nombre del usuario.

## Por qué todavía no se convoca

La regla de la fase exige que las tres capacidades marcadas
`MANDATORY_AT_OWNER_PHASE` funcionen antes de cerrar F004. Una de ellas,
**WAREHOUSE CREATE**, no tiene superficie de navegador: no hay botón, ni diálogo, ni
formulario. Las otras dos existen y están pendientes de confirmación humana, pero
convocar una UAT sabiendo que un tercio del guion es imposible de ejecutar solo gastaría
el tiempo del usuario.

## Guion previsto para la primera ronda (cuando el gate técnico pase)

1. **Editar organización** — abrir, cambiar el nombre a un valor temporal, guardar, 2xx,
   F5, comprobar persistencia, devolver al valor original.
2. **Desactivar sede** — elegir una sede de prueba, desactivar, confirmar, 2xx, F5,
   verla inactiva, comprobar en base de datos; reactivar si el flujo lo permite.
3. **Crear almacén** — abrir almacenes, crear, elegir organización y sede por selector
   humano (nunca escribir UUID), código `UAT-F004-WH-001`, nombre `Almacén UAT F004`,
   guardar, 2xx, verlo en el listado, F5, seguir presente, abrir el detalle.
4. **Rutas negativas** — campo obligatorio ausente, sede inválida, código duplicado,
   recurso inexistente, sin sesión. Todas deben dar 4xx controlado, nunca 500.
5. **Network y Console** — 0 errores 404/500 inesperados, 0 crashes de React.

## Registro de rondas

| Ronda | Fecha | Resultado | Defectos |
|---|---|---|---|
| — | — | no ejecutada | — |
