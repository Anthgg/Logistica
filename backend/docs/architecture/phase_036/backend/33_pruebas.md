# Pruebas

`tests/test_logistics_phase036.py` cubre decimales, máquina de estados, metadata, RBAC/step-up, OpenAPI, calendario/disponibilidad, límites físicos, integración OC→aviso→allocation→submit, aislamiento por tenant, solapamiento de placa/conductor y catálogo de jobs.

La prueba integrada usa cantidad base exacta y demuestra que una segunda reserva que excede la OC falla. Se ejecuta en SQLite para regresión rápida y en PostgreSQL migrado para semántica real de locks, UUID y JSONB.

También se ejecutan suites de fases 020, 034 y 035 para detectar regresiones en documentos, procurement y componentes reutilizados.

