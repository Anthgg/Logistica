# Contratos de healthcheck

- PostgreSQL: `pg_isready` con el usuario y la base configurados.
- Backend: `GET http://127.0.0.1:8000/api/health`.
- Frontend: `GET http://127.0.0.1:8080/`.

Compose no inicia el backend hasta que PostgreSQL está saludable ni el frontend
hasta que el backend está saludable. El servicio `evaluation` está detrás del
perfil homónimo y nunca forma parte del arranque ordinario.
