# 20 — Integración Futura: Calidad e Inventario

## Movimientos de Inventario Reales — Fases 041–046
Al confirmar la Nota de Ingreso (NI) en producción:
1. Se crean movimientos de stock tipo `INGRESO_RECEPCION` en el módulo de inventario
2. Los productos pasan de estado `PENDIENTE_PUTAWAY` a `EN_UBICACION`
3. Se asignan ubicaciones físicas en el almacén (slots/pallets)

## Gestión de Cuarentena — Fase 044+
Cuando una NC indica disposición `CUARENTENA`:
1. El módulo de calidad bloquea el lote físicamente
2. Se crea una partición de stock `BLOQUEADO_CALIDAD`
3. Solo el inspector autorizado puede liberar o rechazar el lote

## Liberación de Producto Post-Inspección — Fase 044+
Flujo de aprobación:
```
NC emitida → Cuarentena → Análisis de calidad → Aprobación / Rechazo
                                                       ↓             ↓
                                              Ingresa a stock    Devolución/Destrucción
```

## Integración con Módulo de Proveedores — Fase futura
- Las diferencias del DIF alimentarán automáticamente el módulo de reclamos a proveedores
- Métricas de confiabilidad de proveedor (% de diferencias, % de NC)
- Los datos históricos de CIT/CPV/AREC contribuirán al score de puntualidad del transportista
