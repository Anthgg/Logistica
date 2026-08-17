# Conexiones de Base de Datos y Estrategia de Pooling

## 1. Métodos de Conexión

Supabase provee dos modalidades principales de acceso a la base de datos PostgreSQL:

1. **Conexión Directa / Session Pooler (Puerto 5432):**
   - Adecuado para aplicaciones con pool persistente y para ejecución de migraciones DDL con Alembic que requieren transacciones de nivel de sesión y `CREATE/ALTER TABLE`.
   - Utilizado por: **Google Cloud Run** y **Alembic Release Jobs**.

2. **Transaction Pooler (PgBouncer en Puerto 6543):**
   - Adecuado para arquitecturas altamente serverless con miles de conexiones concurrentes efímeras (AWS Lambda / Edge Functions).
   - En nuestro caso, Cloud Run administra instancias con concurrencia de hasta 80 peticiones por contenedor y mantiene un pool SQLAlchemy acotado (`pool_size=5`, `max_overflow=10`).

---

## 2. Configuración de SQLAlchemy Pooling

En `backend/app/database/session.py` y `backend/app/core/config.py`:

```python
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,          # False en producción
    pool_pre_ping=True,                   # Verifica la salud de la conexión antes del checkout
    pool_size=settings.DATABASE_POOL_SIZE,# 5 conexiones permanentes por instancia Cloud Run
    max_overflow=settings.DATABASE_MAX_OVERFLOW, # 10 conexiones adicionales bajo carga pico
    pool_timeout=settings.DATABASE_POOL_TIMEOUT, # 30 segundos de espera máxima
    pool_recycle=settings.DATABASE_POOL_RECYCLE, # 1800 segundos (30 min) para reciclar conexiones inactivas
)
```

### Cálculo de Conexiones en Cloud Run:
- Conexiones por instancia de contenedor: `5 (base) + 10 (overflow) = 15 máx`.
- Con `min-instances: 0` y `max-instances: 5`, la carga máxima teórica es `5 * 15 = 75 conexiones`, perfectamente dentro del límite del plan Supabase (disponible para 200+ conexiones en PostgreSQL 17).

---

## 3. Parámetros de Seguridad y SSL

- Protocolo: `postgresql+psycopg://`
- Driver: **Psycopg 3.3.4**
- Cifrado en tránsito: SSL/TLS obligatorio (`sslmode=require`).
- Verificación de certificados: Habilitada por defecto por el driver en conexiones remotas.
