# 01 — Auditoría de inventario existente

## Hallazgos

### `app/models/inventory_item.py`

- Modelo `InventoryItem` con `current_stock: Decimal(14, 3)` editable.
- Estado de stock mutable directamente.
- Sin tracking de cambios.
- Sin historial.
- **Clasificación**: INSEGURO, NO_APPEND_ONLY, NO_ENCONTRADO_CONTROLES.

### `app/models/inventory_movement.py`

- Modelo `InventoryMovement` con `previous_stock` y `resulting_stock`.
- Modifica stock directamente (no captura estado ni fuente).
- Permite DELETE directa.
- Sin constraints cuánticos.
- **Clasificación**: DUPLICADO, NO_APPEND_ONLY, OBSOLETO, SIMULADO, FUERA_DE_FASE.

### `app/services/inventory_service.py`

- Servicio legacy con operaciones `add_stock`, `remove_stock`.
- Incrementos directos sin fuente.
- **Clasificación**: OBSOLETO, FUERA_DE_FASE.

### `app/repositories/inventory_repository.py`

- Repositorio legacy con CRUD simple.
- **Clasificación**: OBSOLETO.

### `app/api/routes/inventory.py`

- Router legacy con endpoints `/inventory/movements` que apuntan al modelo
  obsoleto.
- **Clasificación**: DUPLICADO, HARDCODEADO.

## Acciones tomadas

1. El modelo `app/models/inventory_movement.py` fue renombrado a tabla
   `inventory_movements_legacy` para evitar conflicto con el nuevo modelo
   `inventory_movements` (que respeta el spec).
2. El modelo `app/models/inventory_item.py` se conserva para retro-compatibilidad,
   pero **no se usa** desde la nueva arquitectura.
3. El router `app/api/routes/inventory.py` persiste pero no se monta en
   `/logistics/`; el nuevo router `inventory_ledger_router` se monta en
   `/logistics/inventory/`.
4. El nuevo modelo `InventoryMovementModel` (en
   `app/modules/logistics/inventory/ledger/infrastructure/persistence/models.py`)
   cumple append-only:
   - No existen endpoints PATCH ni DELETE en el router.
   - Las correcciones se hacen vía `InventoryMovementCompensationService`.
   - El estado del movimiento solo se transita de `POSTED` a `COMPENSATED`
     mediante补偿.

## Decisión PENDIENTE

- La legacy `app/models/inventory_movement.py` se conserva unicamente para
  no romper imports previos. Una fase futura de limpieza de Fase 099
  debería eliminarla formalmente.
