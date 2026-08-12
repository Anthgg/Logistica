# 03. Límites con Fases 039, 040 y 043

```mermaid
flowchart LR
  P38["038 descarga"] --> H["Contrato read-only"] --> P39["039 escaneo/recepción"]
  P39 --> P40["040 calidad"]
  P39 --> P43["043 inventario"]
```

Fase 038 termina al completar descarga y liberar muelle. Solo entrega datos esperados y contexto; no recibe cantidades, no decide aceptación y no mueve existencias.

