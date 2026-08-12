"""Phase 037 — Gate Control (Control de Puerta).

This package registers physical vehicle arrival at a warehouse gate,
runs the configurable verification checklist, records the guard's
decision and issues the immutable CPV document.

Explicitly out-of-scope for Phase 037:
- Dock assignment / dock reservation
- Unloading start / end
- Receiving quantities
- Physical lots, serial numbers or pallets
- Inventory mutations

Server-authoritative clock is used for arrived_at.
Guard identity is derived from the authenticated session, never from
a request payload field.
"""
