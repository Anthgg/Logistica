# 28 — Suite de Pruebas Unitarias e Integración (`test_logistics_phase026.py`)

## 1. Cobertura de Pruebas Automáticas

La suite de pruebas en `backend/tests/test_logistics_phase026.py` contiene 22 casos de prueba distribuidos en 8 clases principales:

```python
class TestRucImportService:
    @pytest.mark.asyncio
    async def test_anomaly_detection_triggers_error(self, db_session):
        import_service = RucRegistryImportService()
        with pytest.raises(RucImportAnomalousRowCountError):
            await import_service.validate_and_activate(db_session, new_dataset_id)
```

---

## 2. Resumen de Clases de Prueba

1. `TestRucValidation`: Validación sintáctica y algoritmo Módulo 11 de `PeruvianRucValidator`.
2. `TestRucParser`: Streaming parsing de padrón general y locales anexos.
3. `TestSafeZipDownloader`: Validación de hosts HTTPS autorizados y bloqueo de URLs de terceros.
4. `TestSafeZipExtractor`: Seguridad anti ZIP Bomb (relación compresión, límite 2GB) y Anti Path Traversal.
5. `TestRucLookupCache`: Generación de claves namespace, expiración y negative caching.
6. `TestRucPolicies`: Lógica de `RucStalenessPolicy` y `RucConfidencePolicy`.
7. `TestFakeRucProvider`: Resiliencia de proveedor simulado y fallback.
8. `TestRucServicesIntegration`: Flujo completo de consulta, ingesta y verificación de socios.
