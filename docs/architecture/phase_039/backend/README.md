# Fase 039 — Backend de recepción por escaneo

Implementación backend-only. No crea stock, kardex, cuarentena, putaway, lotes o series maestros ni actas de diferencia. La migración queda preparada y no se ejecuta en producción.

## Invariantes

- Decimal y Numeric para cantidades; nunca float.
- Actor y reloj proceden del servidor.
- Eventos append-only con compensación.
- Resolución exacta y tenant-scoped; nunca crea productos.

### 1. Descarga a recepción

```mermaid
flowchart LR
  A["Descarga a recepción"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 2. Fuente a líneas

```mermaid
flowchart LR
  A["Fuente a líneas"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 3. Sesión a evento

```mermaid
flowchart LR
  A["Sesión a evento"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 4. Código a producto

```mermaid
flowchart LR
  A["Código a producto"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 5. Escaneo unitario

```mermaid
flowchart LR
  A["Escaneo unitario"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 6. Escaneo por cantidad

```mermaid
flowchart LR
  A["Escaneo por cantidad"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 7. Escaneo de empaque

```mermaid
flowchart LR
  A["Escaneo de empaque"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 8. Captura de lote

```mermaid
flowchart LR
  A["Captura de lote"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 9. Captura de serie

```mermaid
flowchart LR
  A["Captura de serie"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 10. Captura de vencimiento

```mermaid
flowchart LR
  A["Captura de vencimiento"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 11. Comparación

```mermaid
flowchart LR
  A["Comparación"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 12. Compensación

```mermaid
flowchart LR
  A["Compensación"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 13. Recepción parcial

```mermaid
flowchart LR
  A["Recepción parcial"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 14. Recepción total

```mermaid
flowchart LR
  A["Recepción total"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 15. Candidato

```mermaid
flowchart LR
  A["Candidato"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 16. Snapshot

```mermaid
flowchart LR
  A["Snapshot"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 17. Handoff 040

```mermaid
flowchart LR
  A["Handoff 040"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 18. Handoff 046

```mermaid
flowchart LR
  A["Handoff 046"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

### 19. Límite inventario

```mermaid
flowchart LR
  A["Límite inventario"] --> B["Validación backend"] --> C["Snapshot o proyección"]
```

