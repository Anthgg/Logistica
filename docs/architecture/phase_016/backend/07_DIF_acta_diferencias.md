# 07 — DIF: Acta de Diferencias

## Propósito
El **DIF** registra formalmente las discrepancias detectadas durante la recepción: faltantes, sobrantes, productos dañados o caducados respecto a la OC o guía de remisión.

## Campos Clave

| Campo | Descripción |
|---|---|
| `reception_reference` | AREC relacionada |
| `report_date` | Timestamp del reporte de diferencias |
| `supplier_name` | Proveedor afectado |
| `carrier_name` | Transportista responsable |
| `differences[]` | Listado de diferencias detectadas |
| `immediate_action` | Acción inmediata tomada o recomendada |

## Tipos de Diferencia (`difference_type`)
| Tipo | Descripción |
|---|---|
| `FALTANTE` | Se recibió menos de lo esperado |
| `SOBRANTE` | Se recibió más de lo esperado |
| `DANO` | Producto recibido con daño físico |
| `CADUCADO` | Producto fuera de fecha de vencimiento |
| `PRODUCTO_INCORRECTO` | Producto diferente al pedido |

## Severidad
`BAJA` → `MEDIA` → `ALTA` → `CRITICA`

Las diferencias `CRITICA` se resaltan en rojo en la plantilla (`class="difference-critical"`).

## Relaciones Documentales
- **Depende de:** AREC
- **Puede originar:** NC (si la diferencia es de calidad)
- **Precede a:** Módulo de Reclamos a Proveedor (Fase futura)
