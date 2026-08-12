# Estados y revisiones

Estados del aviso: `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `REQUIRES_CHANGES`, `APPROVED`, `READY_FOR_SCHEDULING`, `SCHEDULED`, `CONFIRMED` y `CANCELLED`. La máquina de estados rechaza atajos y cualquier transición desde cancelado.

Al enviar, la revisión se congela, se calcula SHA-256 y las allocations `HELD` pasan a `ACTIVE`.
