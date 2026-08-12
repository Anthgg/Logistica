# 23 — Publicación transaccional

`InventoryMovementPostingService.post`:

1. Recibir `PostingRequest`.
2. Resolver idempotencia.
3. Bloquear source.
4. Resolver adapter.
5. Construir líneas.
6. Validar.
7. Bloquear partición.
8. Reservar secuencia.
9. Reservar código MOV.
10. Crear snapshot.
11. Canonicalizar.
12. Calcular `previous_movement_hash`.
13. Calcular `movement_hash`.
14. Insertar movimiento, líneas, fuentes.
15. Actualizar partición.
16. Marcar request POSTED.
17. Publicar outbox.
18. Auditar.
19. Commit.

Todo o nada. Outbox transaccional.
