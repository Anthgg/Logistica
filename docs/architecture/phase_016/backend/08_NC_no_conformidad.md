# 08 — NC: Informe de No Conformidad

## Propósito
La **NC** (No Conformidad) es un documento de la **Familia QUALITY** (no INBOUND). Se emite cuando un inspector de calidad certifica que un lote o producto no cumple los estándares requeridos, registrando el hallazgo y la disposición propuesta.

## Familia QUALITY vs INBOUND
| Aspecto | INBOUND | QUALITY |
|---|---|---|
| Familia documental | `INBOUND` | `QUALITY` |
| Tipo operacional | Logístico / Recepción | Calidad / Inspección |
| Emitido por | Almacenero receptor | Inspector de Calidad |

## Campos Clave

| Campo | Descripción |
|---|---|
| `reception_reference` | AREC relacionada |
| `detection_date` | Timestamp del hallazgo |
| `non_conformity_type` | Tipo de NC |
| `severity` | BAJA / MEDIA / ALTA / CRITICA |
| `supplier_name` | Proveedor |
| `inspector_name` | Inspector que certifica la NC |
| `unfulfilled_requirement` | Requisito incumplido |
| `description` | Descripción detallada del hallazgo |
| `affected_items[]` | Productos afectados con cantidad y disposición |

## Tipos de No Conformidad
- `DANO_EMBALAJE_O_PRODUCTO`
- `TEMPERATURA_FUERA_RANGO`
- `PRODUCTO_CADUCADO`
- `ETIQUETADO_INCORRECTO`
- `CONTAMINACION`
- `FALTA_DE_DOCUMENTACION`

## Disposiciones Propuestas
- `CUARENTENA` — Bloqueo temporal para análisis
- `RECHAZO` — Devolución al proveedor
- `DESTRUCCION` — Eliminación controlada
- `REPROCESO` — Re-acondicionamiento

> ⚠️ En Fase 016 la NC es un documento de registro. El bloqueo real de producto en inventario queda diferido a Fases 044–046 (Gestión de Calidad).
