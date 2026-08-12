# 05 — Optimización de Contenedores Docker

## Características del Dockerfile
* **Multi-Stage Build:** `builder` para compilación e instalación de dependencias en un virtualenv estático, y `runtime` ligero como imagen final.
* **Usuario No-Root:** Ejecución bajo el usuario de sistema `appuser:appgroup` (UID `10001`).
* **Variables de Entorno Estándar:** `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`.
* **Puerto Abierto:** `8080` (estándar de Google Cloud Run).
* **Health Check de Contenedor:**
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8080') + '/health', timeout=4)"
  ```
