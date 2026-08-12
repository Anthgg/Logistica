# 12 — Seguridad de Infraestructura e Imagen

## Prácticas Enforzadas
1. **Sin Secretos Cifrados ni Planos en Git:** Todo secreto (`DATABASE_URL`, `SECRET_KEY`, `CSRF_SECRET`) se almacena en **Google Secret Manager**.
2. **Imagen Contenedora Asegurada:**
   * Ejecución bajo usuario no-root (`appuser`, UID 10001).
   * Exclusión de herramientas de desarrollo, librerías de prueba y archivos de código fuente no requeridos en runtime mediante `.dockerignore`.
   * Ausencia de archivos de desarrollo (`.env`, `.git`, `.venv`).
3. **Imputabilidad y Trazabilidad:** Inyección de `request_id` y `correlation_id` en todas las respuestas HTTP y registros estructurados.
