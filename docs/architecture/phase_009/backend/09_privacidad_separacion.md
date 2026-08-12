# 09 — Privacidad y Aislamiento Estricto de Datos Biométricos

## Principios de Privacidad Enforzados

1. **Aislamiento de Esquemas:** Las tablas logísticas (`warehouses`, `shipments`, `logistics_routes`, `incidents`, `logistics_roles`) NO poseen columnas biométricas, embeddings, ni imágenes.
2. **Identificadores Opacos:** Los vínculos entre decisiones de seguridad y acciones logísticas se realizan únicamente mediante `user_id`, `session_id`, `challenge_id` y `audit_event_id`.
3. **Auditoría Limpia:** Los registros de auditoría registran la decisión (`STEP_UP_PASSED`, `RISK_HIGH`), pero NUNCA contienen embeddings, fotos faciales ni textos capturados por teclado.
