# 06 — Configuración de Google Cloud Run

## Parámetros de Servicio por Ambiente

| Configuración | Staging (`proyecto-t1-api-staging`) | Producción (`autenticacion-continua-api`) |
| :--- | :--- | :--- |
| **Región** | `southamerica-west1` | `southamerica-west1` |
| **CPU** | 1.0 vCPU | 2.0 vCPU |
| **Memoria RAM** | 1.0 GiB | 2.0 GiB |
| **Concurrencia Máxima** | 80 solicitudes / instancia | 80 solicitudes / instancia |
| **Instancias Mínimas (`min-instances`)** | 0 (Scale to zero) | 1 (Evita Cold Start) |
| **Instancias Máximas (`max-instances`)** | 5 | 20 |
| **Timeout de Solicitud** | 60s | 60s |
| **Cuenta de Servicio** | `sa-staging@...iam.gserviceaccount.com` | `sa-production@...iam.gserviceaccount.com` |
