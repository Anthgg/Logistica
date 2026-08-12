# 18. Readiness

Las definiciones son configurables por organización/muelle y los resultados son inmutables. Checks de Gate, vehículo en dock y dock operativo se derivan del backend; el resto exige registro explícito.

```mermaid
flowchart TD
  D["Definiciones"] --> R["Resultados"]
  R --> M{"Faltantes"}
  R --> B{"Bloqueos no aprobados"}
  M --> P["PENDING"]
  B --> X["BLOCKED"]
  M -->|no| OK["READY"]
```

