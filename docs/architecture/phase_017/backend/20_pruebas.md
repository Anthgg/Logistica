# Cobertura de Pruebas Unitarias e Integración (Phase 017)

## Resumen de la Suite
Las pruebas se ubican en `tests/test_logistics_phase017.py` con una cobertura de 42 casos exitosos:
- **Pruebas de Validadores**: Verifican consistencia matemática en ajustes, mermas y diferencias en recepciones.
- **Pruebas de Esquemas**: Aseguran el rechazo de payloads inconsistentes (misma bodega origen/destino, items vacíos).
- **Pruebas de Renderizado**: Verifican que WeasyPrint o el generador de fallback compile exitosamente los 8 templates HTML.
- **Pruebas de Conteo Ciego**: Confirman que el backend oculta los datos de stock teórico cuando el modo ciego está activo.
- **Pruebas de Seguridad**: Validan el retorno de código `401 Unauthorized` en solicitudes sin credenciales.
- **Prueba de No Operación**: Garantiza que ningún endpoint de rendering altere tablas de stock o saldos reales.
