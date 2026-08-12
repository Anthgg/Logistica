# Arquitectura de Plantillas de Inventario (Phase 017)

## Estructura de Directorios
Las plantillas se organizan bajo el motor de renderizado central en:
```
templates/inventory/
├── shared/
│   ├── inventory.css (Estilos específicos)
│   └── components/ (Fragmentos reutilizables)
├── location_label/
│   └── eub_v1.html
├── putaway_order/
│   └── put_v1.html
├── movement/
│   └── mov_v1.html
├── adjustment/
│   └── aji_v1.html
├── count/
│   └── cnt_v1.html
├── difference/
│   └── adi_v1.html
├── transfer/
│   └── tra_v1.html
└── transfer_receipt/
    └── crt_v1.html
```

## Integración con el Motor
- **Jinja2 + WeasyPrint**: Se extienden los estilos base mediante `shared/print.css`.
- **Watermark y QR**: Todas las plantillas heredan la lógica de marcas de agua (`VISTA PREVIA`) y el código QR de demostración dinámico.
