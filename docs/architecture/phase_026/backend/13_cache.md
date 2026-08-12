# 13 — Capa de Caché L1/L2 y Tagging por Versión (`RucLookupCache`)

## 1. Estrategia de Caché Multinivel

El servicio de consulta de RUC requiere latencias sub-15ms. Para lograrlo, implementa una arquitectura de caché en dos niveles:
- **L1 (In-Memory Local)**: Almacenamiento local LRU en la instancia de la aplicación (TTL 60s) para consultas ultra-frecuentes.
- **L2 (Redis Distribuido)**: Caché compartida entre réplicas del microservicio (TTL 86400s / 24 hrs).

```python
class RucLookupCache:
    NAMESPACE_PREFIX = "ruc"

    @classmethod
    def build_key(cls, dataset_version_id: UUID, normalized_ruc: str) -> str:
        return f"{cls.NAMESPACE_PREFIX}:{dataset_version_id}:{normalized_ruc}"

    @classmethod
    async def get(cls, dataset_version_id: UUID, normalized_ruc: str) -> dict | None:
        key = cls.build_key(dataset_version_id, normalized_ruc)
        return await redis_client.get_json(key)

    @classmethod
    async def set(cls, dataset_version_id: UUID, normalized_ruc: str, data: dict, ttl_seconds: int = 86400):
        key = cls.build_key(dataset_version_id, normalized_ruc)
        await redis_client.set_json(key, data, expire=ttl_seconds)
```

---

## 2. Negative Caching (Caché de Negativos)

Para prevenir ataques de denegación de servicio (DoS) mediante consultas masivas de RUCs sintácticamente válidos pero inexistentes en la base de datos, el sistema guarda las búsquedas fallidas con un TTL reducido:

```python
if record is None:
    await RucLookupCache.set_negative(dataset_version_id, normalized_ruc, ttl_seconds=300)
    raise RucNotFoundError(f"RUC {normalized_ruc} no encontrado en el padrón activo.")
```

---

## 3. Invalidación Instantánea por Tagging de Versión

Al incluir `dataset_version_id` en la clave de caché (`ruc:{dataset_version_id}:{normalized_ruc}`), la conmutación a un nuevo dataset invalida automáticamente la caché previa sin necesidad de ejecutar barridos `KEYS ruc:*` costosos en Redis.
