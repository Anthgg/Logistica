# 02 — Arquitectura de Plantillas de Ingreso (Fase 016)

## Árbol de Plantillas

```
templates/
├── base/
│   └── base_v1.html              ← Base compartida (Fase 014)
├── shared/
│   └── print.css                 ← Estilos de impresión (Fase 014)
├── inbound/
│   ├── shared/
│   │   └── inbound.css           ← Estilos específicos de ingreso (Fase 016)
│   ├── appointment/
│   │   └── cit_v1.html           ← inbound.cit v1.0.0
│   ├── gate_control/
│   │   └── cpv_v1.html           ← inbound.cpv v1.0.0
│   ├── reception_act/
│   │   └── arec_v1.html          ← inbound.arec v1.0.0
│   ├── inbound_note/
│   │   └── ni_v1.html            ← inbound.ni v1.0.0
│   └── differences/
│       └── dif_v1.html           ← inbound.dif v1.0.0
└── quality/
    └── non_conformity/
        └── nc_v1.html            ← quality.nc v1.0.0
```

## Herencia Visual
Todas las plantillas incluyen `shared/print.css` e `inbound/shared/inbound.css` con `{% include %}` de Jinja2.

## TEMPLATE_MAP actualizado
| Clave | Ruta |
|---|---|
| `base.document` | `base/base_v1.html` |
| `purchasing.*` | `purchasing/...` (Fase 015) |
| `inbound.cit` | `inbound/appointment/cit_v1.html` |
| `inbound.cpv` | `inbound/gate_control/cpv_v1.html` |
| `inbound.arec` | `inbound/reception_act/arec_v1.html` |
| `inbound.ni` | `inbound/inbound_note/ni_v1.html` |
| `inbound.dif` | `inbound/differences/dif_v1.html` |
| `quality.nc` | `quality/non_conformity/nc_v1.html` |
