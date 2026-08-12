# 20. Registro de Decisiones de Arquitectura Pendientes (ADR)

## 📋 Registro de Decisiones Diferidas

A continuación se detallan las decisiones de diseño técnico que han sido diferidas a fases posteriores del proyecto:

---

### ADR-021-01: Certificados Digitales PKCS#12 (`.pfx` / `.p12`) para Firma Digital SUNAT
* **Estado**: Differed (Diferido a Fase 026 / Fase 030).
* **Contexto**: La Fase 021 administra la **firma visual** (imagen sanitizada del trazo o sello) y la resolución de apoderados autorizados. Sin embargo, para la emisión de Comprobantes de Pago y Guías de Remisión Electrónicas ante SUNAT se requiere la firma criptográfica mediante Certificado Digital X.509 / PKCS#12 con clave privada.
* **Decisión Diferida**: El almacenamiento del archivo cifrado `.pfx` y su contraseña en un HSM (Hardware Security Module) o AWS KMS se implementará en la Fase 026/030.

---

### ADR-021-02: Soporte Multipaís / Multirregión (Tributación Internacional)
* **Estado**: Deferred.
* **Contexto**: La Fase 021 incluye campos de soporte regional (`country_code`, `locale`, `timezone`, `default_currency`), pero el validador Módulo 11 está configurado por defecto para el RUC de Perú (`PE`).
* **Decisión Diferida**: En caso de expandir la plataforma a operaciones en otros países de LATAM (ej. NIT en Colombia, RFC en México, RUT en Chile), se creará una fábrica de validadores tributarios por código ISO de país (`country_code`).

---

### ADR-021-03: Sincronización Automática de Padrón RUC mediante CDN/Local SQLite
* **Estado**: Deferred (Diferido a Fase 026).
* **Contexto**: El Padrón RUC de SUNAT contiene más de 6 millones de registros. Descargar y consultar el padrón completo localmente mediante un motor SQLite o DuckDB evitaría cualquier consulta web externa.
* **Decisión Diferida**: Se evaluará el costo de almacenamiento y actualización diaria del padrón en la Fase 026.
