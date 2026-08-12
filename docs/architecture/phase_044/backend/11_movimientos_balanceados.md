# 11 — Movimientos balanceados (doble efecto)

Toda línea mueve cantidad desde un origen hacia un destino. Las reglas:

- **ENTRY** (entrada): origen = frontera externa, destino = posición interna.
- **EXIT** (salida): origen = posición interna, destino = frontera externa.
- **TRANSFER**: origen = posición interna, destino = posición interna.
- **STATE_CHANGE**: origen / destino = misma cantidad, distinta combinación
  de estados.
- **RESERVATION_CHANGE**: cambia estado de disponibilidad, no cantidad.
- **COMPENSATION**: invierte origin y destination.

La cantidad base de origen y destino debe ser idéntica (cuando aplique).
No se permiten δeltas sin contexto.
