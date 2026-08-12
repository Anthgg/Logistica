# 16 — Adaptadores de Proveedores Autorizados y Resiliencia (`RucEnrichmentProvider`)

## 1. Interface de Abstracción `RucEnrichmentProvider`

Para habilitar la consulta en tiempo real de RUCs recién constituidos no presentes en el padrón mensual, el sistema define la interface abstracta `RucEnrichmentProvider`:

```python
class RucEnrichmentProvider(ABC):
    @abstractmethod
    async def lookup_ruc(self, ruc: str) -> RucProviderResult | None:
        pass
```

---

## 2. Implementaciones Incluidas

1. **`NoOpRucProvider`**: Implementación por defecto en entornos donde no se contrate un proveedor API externo. Retorna `None` inmediatamente sin consumir recursos de red.
2. **`FakeRucProvider`**: Implementación mock determinista utilizada en la suite de pruebas automatizadas e integración continua.

```python
class FakeRucProvider(RucEnrichmentProvider):
    def __init__(self, mock_db: dict = None, should_fail: bool = False):
        self.mock_db = mock_db or {}
        self.should_fail = should_fail

    async def lookup_ruc(self, ruc: str) -> RucProviderResult | None:
        if self.should_fail:
            raise RucProviderUnavailableError("Proveedor simulado no disponible.")
        return self.mock_db.get(ruc)
```

---

## 3. Políticas de Resiliencia y Fallback

- **Timeout Estricto**: Máximo 2.0 segundos de tiempo de espera HTTP.
- **Circuit Breaker**: Si el proveedor falla 5 veces consecutivas (`consecutive_failures >= 5`), se desactiva temporalmente por 15 minutos (`status = 'DEGRADED'`).
- **Fallback a Padrón Local**: Ante cualquier fallo del proveedor, la consulta decae transparentemente a los datos locales disponibles.
