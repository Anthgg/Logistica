# 21 — Cantidades y unidades

- Cantidad siempre `Decimal`, nunca `float`.
- `quantity > 0`, `base_quantity > 0`.
- Escala preservada (no redondeo silencioso).
- Sin NaN, sin Infinity.
- Conservar cantidad original, unidad original, conversión.
- `unit_id` y `base_unit_id` siempre presentes.
- Si `unit_id != base_unit_id`, el backend exige un `conversion_rule_id` activo,
  vigente y compatible; el `conversion_snapshot` lo genera el servidor.
- `base_quantity` se calcula en backend (server-derived), nunca del cliente.
- El límite HTTP rechaza de forma recursiva `base_quantity`,
  `conversion_snapshot`, hashes, saldos, riesgo y demás campos derivados.
