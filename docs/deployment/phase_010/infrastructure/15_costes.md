# 15 — Control de Presupuesto y Costes

## Medidas de Control de Gasto en GCP

1. **Límite de Instancias Máximas (`max-instances`):**
   * Staging: Máximo 5 instancias.
   * Producción: Máximo 20 instancias.
2. **Escalado a Cero:** Staging escala a 0 instancias inactivas para eliminar consumo cuando no hay pruebas.
3. **Límite de Presupuesto (GCP Budget Alert):** Notificación automática por correo al alcanzar el 80% del presupuesto mensual estimado.
4. **Política de Limpieza de Imágenes:** Limpieza automática en Artifact Registry conservando las últimas 20 revisiones.
