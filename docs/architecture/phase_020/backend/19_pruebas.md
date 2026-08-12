# 19. Estrategia de Pruebas

La suite de pruebas automatizadas se encuentra en `tests/test_logistics_phase020.py` y cubre los siguientes componentes:

## Casos de Prueba
1. **TestDocumentSnapshot**:
   - Estabilidad del hash criptográfico determinista.
   - Soporte correcto para serialización de Decimal, UUID y DateTime.
2. **TestDocumentLifecycle**:
   - Flujo continuo: Creación -> Preview -> Emisión -> Impresión -> Reimpresión -> Anulación.
   - Verificación de inmutabilidad del snapshot original.
   - Trazabilidad en la bitácora histórica.
3. **TestTalonariosAndZip**:
   - Generación de PDF de talonarios con marcas de reserva.
   - Compilación del archivo ZIP con csv, json y checksums.
4. **TestSecurityGating**:
   - Gating horizontal por organización (Tenant Isolation).
   - Bloqueo de peticiones sin autenticación (401).
