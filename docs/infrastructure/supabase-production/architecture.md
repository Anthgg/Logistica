# Arquitectura de Ambientes · Base de Datos y Runtime

## 1. Topología de Ambientes

```
========================================================================================
DESARROLLO LOCAL & CI
========================================================================================
[ Developer Workstation / CI Runner ]
      │
      ├──> FastAPI (Uvicorn / Docker)
      │       │
      │       └──> SQLAlchemy 2.0 (postgresql+psycopg)
      │               │
      │               └──> PostgreSQL 16.4 Docker Container (localhost:5432)
      │
      └──> Alembic CLI (Single Source of Truth)
              │
              └──> PostgreSQL 16.4 Docker (Local Dev & Test Clean DBs)

========================================================================================
PRODUCCIÓN (LIVE & GATED)
========================================================================================
[ Google Cloud Platform ]                           [ Supabase Managed Database ]
Google Cloud Run                                   Supabase PostgreSQL 17.6
Service: autenticacion-continua-api                Host: db.nrrgwibyiekacisdtgiq.supabase.co
Region: southamerica-west1 (Santiago)             Region: AWS sa-east-1 (São Paulo)
      │                                                   │
      ├──> FastAPI Runtime                                │
      │       │                                           │
      │       └──> SQLAlchemy Connection Pool             │
      │               │                                   │
      │               └─── [ SSL Encrypted Connection ] ──┘ (Port 5432 / Session Pool)
      │
[ Release Migration Pipeline ]
Google Cloud Run Job / Release CLI
      │
      └──> Alembic Release Step (alembic upgrade head)
              │
              └─── [ SSL Encrypted Connection ] ──────────> Supabase PostgreSQL 17.6
========================================================================================
```

---

## 2. Principios de Diseño

1. **Alembic como Única Fuente de Verdad:**
   Todas las definiciones de esquema DDL residen exclusivamente en `backend/alembic/versions`. No existen migraciones SQL manuales ni herramientas secundarias (como Supabase migrations CLI) compitiendo con Alembic.

2. **Supabase como PostgreSQL Estándar Administrado:**
   El backend interactúa con Supabase exclusivamente mediante el protocolo nativo de PostgreSQL usando SQLAlchemy y Psycopg 3 (`postgresql+psycopg://`). No se utiliza el SDK de Supabase (`supabase-py`) para la lógica de datos de negocio.

3. **Sin Supabase Auth:**
   El sistema conserva su propia arquitectura de autenticación y seguridad:
   - Tokens JWT firmados criptográficamente.
   - Rotación estricta de Refresh Tokens en base de datos.
   - Cookies `HttpOnly`, `SameSite=Lax`, `Secure`.
   - Protección contra CSRF con token firmado.
   - Huella de dispositivos y control de accesos RBAC a nivel aplicativo.

4. **Aislamiento Total de Almacenamiento Documental:**
   Los archivos binarios (PDFs, capturas, evidencias) se mantienen bajo el subsistema de almacenamiento configurado (`local` volume / GCS) y no se mezclan con Supabase Storage durante esta fase de baseline de base de datos.
