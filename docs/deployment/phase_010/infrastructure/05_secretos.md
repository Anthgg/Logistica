# 05 — Inyección y Versionado de Secretos (Secret Manager)

## Secretos Registrados

| Nombre del Secreto | Formato / Tipo | Servicio Consumidor | Policy de Rotación |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | String Cifrado | Backend API / Job Migración | 90 días |
| `SECRET_KEY` | String Cifrado (min 16 chars) | Backend Security Middleware | 90 días |
| `CSRF_SECRET` | String Cifrado | CSRF Middleware | 90 días |

## Inyección en Cloud Run
```bash
# Ejemplo de inyección de secretos desde Secret Manager al servicio Cloud Run
gcloud run services update autenticacion-continua-api \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest" \
  --region=southamerica-west1
```
