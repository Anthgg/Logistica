# Fase 038 Backend: operaciones de muelle y descarga

Implementación backend-only para convertir una autorización de ingreso de la Fase 037 en cola interna, plan determinista, asignación segura, ocupación, descarga y liberación de muelle.

## Límites innegociables

- No registra cantidades recibidas, aceptadas o rechazadas.
- No crea lotes, series, pallets, stock ni movimientos de inventario.
- No implementa recepción física de Fase 039.
- Usuarios, estados, timestamps y duraciones son autoritativos del servidor.
- No usa IA ni inventa distancias. La recomendación es determinista y explicable.

## Invariantes

1. Solo un Gate Check-In autorizado puede entrar a cola.
2. El plan tiene hash y TTL; la ejecución revalida disponibilidad y compatibilidad bajo bloqueo.
3. Índices únicos parciales y locks de fila impiden asignación, ocupación, pausa u operación activa duplicada.
4. Readiness y checklist final son persistentes e inmutables; los overrides requieren separación de funciones.
5. La descarga calcula tiempo bruto, pausas y tiempo neto en backend.
6. Cada transición operativa genera evento append-only, outbox y auditoría.

## Estado de entrega

- 21 tablas nuevas y migración reversible `ab380110038dc`.
- 31 permisos RBAC y políticas step-up de riesgo alto/crítico.
- 69 paths OpenAPI relacionados con dock/unloading al cargar la aplicación.
- Jobs persistentes para planes vencidos, movimientos estancados, descargas abandonadas y proyecciones.
- `PENDIENTE_CATÁLOGO_DOCUMENTAL`: no se emite un documento oficial nuevo sin catálogo aprobado.
- `PENDIENTE_APROBACIÓN_DB`: una exclusión GiST por rango podría reforzar intervalos futuros; la entrega no instala `btree_gist` automáticamente.

## Ejecución de jobs

```powershell
python -m app.modules.logistics.inbound.dock_operations.infrastructure.jobs.run_phase038_jobs all
```

## Mapa documental

Los documentos `01` a `50` describen auditoría, arquitectura, modelo, seguridad, integración, pruebas y runbooks. `phase_038_backend_manifest.json` enumera decisiones y archivos relevantes.

