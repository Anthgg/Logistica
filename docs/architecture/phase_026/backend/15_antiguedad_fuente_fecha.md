# 15 — Política de Antigüedad y Obsolescencia de Datos (`RucStalenessPolicy`)

## 1. Clasificación de Niveles de Obsolescencia (`StalenessLevel`)

La política `RucStalenessPolicy` evalúa el tiempo transcurrido desde la fecha de publicación o descarga del padrón activo (`fetched_at` / `source_published_at`):

```python
class StalenessLevel(str, Enum):
    FRESH = "FRESH"        # <= 7 días
    AGING = "AGING"        # 8 a 30 días
    STALE = "STALE"        # 31 a 60 días
    CRITICAL = "CRITICAL"  # > 60 días
```

---

## 2. Reglas de Cálculo en `RucStalenessPolicy`

```python
class RucStalenessPolicy:
    @classmethod
    def calculate(cls, reference_date: datetime, now: datetime = None) -> StalenessLevel:
        now = now or datetime.now(timezone.utc)
        age_days = (now - reference_date).days

        if age_days <= 7:
            return StalenessLevel.FRESH
        elif age_days <= 30:
            return StalenessLevel.AGING
        elif age_days <= 60:
            return StalenessLevel.STALE
        else:
            return StalenessLevel.CRITICAL
```

---

## 3. Impacto Operativo en el Sistema

- **`FRESH` / `AGING`**: Operación normal. El sistema responde con el padrón sin advertencias.
- **`STALE`**: Se registra un log de advertencia `RUC_PADRON_STALE` sugiriendo la ejecución de un nuevo job de importación.
- **`CRITICAL`**: Se emite una alerta de observabilidad de alta prioridad y los endpoints de consulta añaden el encabezado HTTP `X-RUC-Data-Staleness: CRITICAL`.
