# 01. Alcance General del Backend — Proyecto T1

## 1. Inclusiones Generales del Backend

El backend logístico asumirá la responsabilidad total del procesamiento de reglas de negocio, integridad de inventario, validaciones operativas, cálculo de saldos y emisión documental bajo la ruta raíz `/api/logistics`.

- **Maestros Logísticos:** Gestión completa de organizaciones, sedes, almacenes, ubicaciones internas, catálogo de productos, categorías, unidades de medida, conversiones, socios de negocio (proveedores, clientes, transportistas), vehículos y conductores.
- **Flujos de Aprobación Operativa:** Aprobaciones jerárquicas con control de estados para compras, liberación de calidad, despachos y devoluciones.
- **Estados Controlados:** Máquina de estados estricta e inmutable para cada documento u orden operativa.
- **Numeración Documental y Correlativos:** Generación automática de números de documento serie-correlativo (Guías de Remisión, Requerimientos, Órdenes de Compra, Actas de Recepción/Despacho).
- **Motor Documental y Evidencias:** Generación asíncrona de archivos PDF y almacenamiento seguro de imágenes/actas en Almacenamiento de Objetos (Cloud Storage / S3).
- **Auditoría Inmutable:** Registro de auditoría detallado para cada cambio de estado, edición o acción sensible, enlazado al usuario autenticado.
- **Control Fino de Acceso (RBAC + Step-up):** Roles y permisos granulares con requisito de re-autenticación continua/Step-up OTP para acciones de alto riesgo (ajustes de inventario, anulaciones, aprobación de compras).
- **Motor de Inventario:** Cálculo transaccional de stock disponible, reservado, en cuarentena y en tránsito. Soporte nativo para lotes, números de serie y fechas de vencimiento.
- **Operaciones de Almacén:** Gestión completa de órdenes de recepción, inspecciones de calidad, transferencias inter-almacén, picking, packing y salidas.
- **Distribución y Transporte:** Planificación de viajes, asignación de rutas, registro de coordenadas GPS en tiempo real, geocercas, prueba de entrega digital (POD con foto, firma u OTP) y gestión de incidencias.

---

## 2. Exclusiones Explícitas del Lanzamiento Inicial (MVP)

1. **Facturación Electrónica Automática y Emisión SUNAT Comprobantes Pago (Factura/Boleta):**
   - *Motivo:* Complejidad regulatoria PSE/OSE SUNAT. El MVP logístico solo emitirá Guías de Remisión Internas y Documentos de Transporte Logístico.
   - *Fase Futura:* Fase 005 (Integración Tributaria).

2. **Contabilidad Completa, Planillas y Nómina:**
   - *Motivo:* Fuera del dominio logístico y operativo primario.
   - *Fase Futura:* Excluido del núcleo T1 (se integrará vía exportaciones ERP en Fase 006).

3. **Marketplace y Comercio Electrónico B2C:**
   - *Motivo:* El proyecto está enfocado en operaciones B2B y logística propia/tercerizada para AndesLog Operaciones S.A.C.

4. **Optimización con IA y Predicción de Demanda en el MVP:**
   - *Motivo:* Requiere histórico consolidado de datos. El MVP utilizará reglas heurísticas y mínimos/máximos configurados manualmente.
   - *Fase Futura:* Fase 006 (Analítica Avanzada e Inteligencia Artificial).

5. **Motor de Rutado Propio (VRPTW Solvers internos):**
   - *Motivo:* Costo computacional y complejidad de mantenimiento. El MVP utilizará motores de mapas y rutado externos (OpenStreetMap / Valhalla / Mapbox Routing API).

6. **Scraping No Autorizado o Evasión de CAPTCHA:**
   - *Motivo:* Legalidad y estabilidad. Las consultas SUNAT/SUNARP/MTC se realizarán mediante APIs oficiales, padrones reducidos en base de datos o integraciones autorizadas.

7. **Multi-tenancy SaaS Multiempresa Complejo:**
   - *Motivo:* El diseño inicial es monotenant con soporte multisede y multiorganización jerárquica para la operación de la tesis/empresa objetivo.

---

## 3. Restricciones Técnicas

- **Reutilización de Autenticación:** Queda estrictamente prohibido crear un segundo mecanismo de login o sesión. El backend logístico reutilizará exclusivamente las cookies HTTP-only (`access_token_cookie`, `csrf_access_token`) y la dependencia `get_current_user` del backend FastAPI existente.
- **Integridad de Inventario:** El frontend NUNCA calculará el stock disponible ni validará saldos de inventario por sí solo. Toda reserva o movimiento será procesado atómicamente en PostgreSQL mediante transacciones SERIALIZABLE / SELECT FOR UPDATE.
- **Separación de Datos Biométricos:** Los modelos biométricos y plantillas PAD existentes en el backend permanecen aislados en sus respectivas tablas. La API logística interactúa únicamente con el nivel de confianza (score) retornado por el middleware de autenticación continua.
