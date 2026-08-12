# Nginx

La configuración efectiva está en `frontend/nginx.conf`. Sirve la SPA en el
puerto no privilegiado 8080, comprime respuestas, evita cachear indefinidamente
`index.html`, mantiene caché largo para assets con hash y añade CSP, protección
MIME, política de referencia y permisos de cámara limitados al propio origen.

`connect-src` admite el backend local y hosts HTTPS de Cloud Run. No habilita
`unsafe-eval`, micrófono ni orígenes HTTP externos.
