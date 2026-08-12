# 11. Matriz de Fases y Distribución por MVP — Proyecto T1

## 1. Clasificación por Etapa Operativa

### MVP 1 — Base, Seguridad y Maestros Logísticos
- **Enfoque:** Infraestructura de backend, integración con la autenticación continua existente, gestión de datos maestros y servicios transversales.
- **Módulos Incluidos:**
  - `logistics/configuration`, `organizations`, `branches`, `warehouses`, `locations`.
  - `logistics/products`, `units`.
  - `logistics/business-partners`, `suppliers`, `customers`, `carriers`, `vehicles`, `drivers`.
  - `logistics/documents` (Motor PDF), `files` (Cloud Storage), `audit` (Auditoría).
  - `logistics/integrations` (Consulta RUC SUNAT / Padrón, Verificación de Flota y Brevetes).
- **Criterio de Salida:** Maestros cargados, verificación de RUC funcionando, motor PDF operativo y middleware RBAC/Step-Up integrado.

### MVP 2 — Abastecimiento, Almacén, Inventario y Despacho
- **Enfoque:** Operación completa dentro del almacén central/cedi.
- **Módulos Incluidos:**
  - `logistics/purchases`, `purchase_orders`.
  - `logistics/inbound`, `receptions`, `quality`.
  - `logistics/inventory`, `stock`, `transfers` (Kardex, Lotes, Series, Reservas atómicas).
  - `logistics/outbound`, `picking`, `packing`, `dispatches`.
- **Criterio de Salida:** Kardex de inventario transaccional 100% confiable, recepción en muelle y emisión de Guía de Remisión de Salida.

### MVP 3 — Distribución, Telemetría GPS, Entrega y Devoluciones
- **Enfoque:** Operación en campo, transporte y última milla.
- **Módulos Incluidos:**
  - `logistics/trips`, `routes`, `gps`.
  - `logistics/deliveries`, `returns`, `incidents`, `notifications`.
- **Criterio de Salida:** Rastreabilidad en vivo por GPS, prueba de entrega digital (POD con foto/OTP) y flujo de devoluciones cerrado.

### Consolidación — KPIs, Optimización y Piloto de Producción
- **Enfoque:** Estabilidad, reportabilidad avanzada y despliegue final en Cloud Run.
- **Módulos Incluidos:**
  - `logistics/kpis` (OTIF, ERI, Tiempos de ciclo).
  - Exportaciones masivas a Excel/CSV.
  - Pruebas E2E y prueba piloto congelada para la tesis.
- **Criterio de Salida:** Métricas validadas, aprobación técnica y cierre documental.
