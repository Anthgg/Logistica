# 09 — Componentes HTML Reutilizables

## Componentes Planificados (Implementación Completa en Fase 017+)

Los siguientes bloques son fragmentos Jinja2 reutilizables que se incluyen en múltiples plantillas de ingreso. En Fase 016 su contenido está integrado directamente en cada template; se refactorizarán como `{% include %}` independientes en fases posteriores.

| Componente | Archivo | Usado en |
|---|---|---|
| `vehicle_information` | `components/vehicle_information.html` | CPV, AREC |
| `driver_information` | `components/driver_information.html` | CPV (con masking automático) |
| `seal_control` | `components/seal_control.html` | CPV |
| `time_milestones` | `components/time_milestones.html` | AREC |
| `quantity_comparison` | `components/quantity_comparison.html` | AREC, NI |
| `evidence_references` | `components/evidence_references.html` | DIF, NC |

## CSS Compartido — `inbound.css`
El archivo `inbound/shared/inbound.css` define:
- `.inbound-box` / `.inbound-title` — contenedores de sección azul oscuro
- `.milestone-timeline` — tabla de tiempos de descarga
- `.seal-badge` + `.seal-matched` / `.seal-broken` / `.seal-mismatched` — badges de estado de precinto
- `.privacy-notice` — aviso de datos enmascarados
- `.quantity-table` — tabla de cantidades expected/received/accepted
- `.difference-critical` — resaltado rojo para diferencias críticas
