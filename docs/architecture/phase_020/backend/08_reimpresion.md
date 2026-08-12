# 08. Reimpresión Controlada

La reimpresión de copias físicas oficiales requiere la justificación explícita del operador y está protegida por políticas de autenticación continua.

## Reglas Técnicas
1. **Paso Step-Up obligatorio**: La acción requiere nivel de riesgo `HIGH` y validación de OTP o prueba biométrica.
2. **Snapshot original**: Se renderiza usando el snapshot inmutable de emisión original, prohibiendo el uso de datos actuales de base de datos.
3. **Marca distintiva**: El PDF resultante se genera con la marca de agua `REIMPRESIÓN - COPIA N° X` (donde X es el número de reimpresión incrementado).
4. **Registro de artefacto**: Cada reimpresión genera un nuevo artefacto de tipo `REPRINT_PDF` en la base de datos.
