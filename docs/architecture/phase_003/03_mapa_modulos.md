# 03. Mapa de Módulos

| Módulo | Responsabilidad | Dependencias |
|--------|----------------|--------------|
| **documents** | Generación, emisión, anulación y almacenamiento de documentos logísticos (guías, actas, manifiestos). | files (storage), audit (registro) |
| **routes_module** | Cálculo de rutas, geocodificación y map-matching via proveedores externos. | integrations (proveedores) |
| **files** | Almacenamiento, validación y gestión de PDFs, imágenes, firmas y evidencias. | Ninguna (servicio base) |
| **audit** | Registro inmutable de eventos logísticos. Reutiliza AuditService existente via adaptador. | Ninguna (servicio transversal) |
| **integrations** | Adaptadores para SUNAT, SUNARP, MTC, SMS, geocodificación y otros servicios externos. | Ninguna (servicio base) |

## Dependencias entre módulos

```
documents ──→ files
documents ──→ audit
routes_module ──→ integrations
```

Los módulos `files`, `audit` e `integrations` no dependen de otros submódulos logísticos.